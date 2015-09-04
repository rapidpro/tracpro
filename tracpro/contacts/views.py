from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import pycountry

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import get_obj_cacheable
from dash.utils.sync import ChangeType

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.translation import ugettext_lazy as _

from smartmin.users.views import (
    SmartListView, SmartCreateView, SmartReadView, SmartUpdateView,
    SmartDeleteView, SmartCRUDL)

from tracpro.polls.models import PollRun, RESPONSE_COMPLETE

from .fields import URN_SCHEME_CHOICES
from .forms import ContactForm
from .models import Contact


class ContactFormMixin(object):
    """
    Mixin for views that use a contact form
    """

    def get_form_kwargs(self):
        kwargs = super(ContactFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if 'initial' in self.request.POST or 'initial' in self.request.GET:
            initial = self.request.POST.get('initial', self.request.GET.get('initial'))
            results = []
            if initial:
                lang = pycountry.languages.get(bibliographic=initial)
                name = lang.name.split(';')[0]
                results.append(dict(id=lang.bibliographic, text=name))
            return JsonResponse(dict(results=results))

        if 'search' in self.request.GET or 'search' in self.request.POST:
            search = self.request.POST.get('search', self.request.GET.get('search'))
            search = search.strip().lower()
            results = []
            for lang in pycountry.languages:
                if len(results) == 10:
                    break
                if len(search) == 0 or search in lang.name.lower():
                    results.append(dict(id=lang.bibliographic, text=lang.name))
            return JsonResponse(dict(results=results))

        return super(ContactFormMixin, self).get(request, *args, **kwargs)


class ContactFieldsMixin(object):

    def get_urn(self, obj):
        # TODO indicate different urn types with icon?
        return obj.get_urn()[1]

    def lookup_field_label(self, context, field, default=None):
        if field == 'urn':
            return _("Phone/Twitter")

        return super(ContactFieldsMixin, self).lookup_field_label(context, field, default)


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('create', 'read', 'update', 'delete', 'list')

    class Create(OrgPermsMixin, ContactFormMixin, SmartCreateView):
        fields = ('name', 'urn', 'region', 'group', 'facility_code', 'language')
        form_class = ContactForm

        def derive_initial(self):
            initial = super(ContactCRUDL.Create, self).derive_initial()
            initial['region'] = self.request.region
            return initial

        def save(self, obj):
            org = self.request.user.get_org()
            self.object = Contact.create(org, self.request.user, obj.name, obj.urn,
                                         obj.region, obj.group, obj.facility_code, obj.language)

    class Update(OrgObjPermsMixin, ContactFormMixin, SmartUpdateView):
        fields = ('name', 'urn', 'region', 'group', 'facility_code', 'language')
        form_class = ContactForm

        def get_queryset(self):
            regions = self.request.user.get_direct_regions(self.request.org)
            queryset = super(ContactCRUDL.Update, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True, region__in=regions)

        def post_save(self, obj):
            obj = super(ContactCRUDL.Update, self).post_save(obj)
            obj.push(ChangeType.updated)
            return obj

    class Read(OrgObjPermsMixin, SmartReadView):

        def derive_fields(self):
            fields = ['urn', 'region', 'group', 'facility_code', 'language',
                      'last_response']
            if self.object.created_by_id:
                fields.append('created_by')
            return fields

        def get_queryset(self):
            regions = self.request.user.get_direct_regions(self.request.org)
            queryset = super(ContactCRUDL.Read, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True, region__in=regions)

        def get_urn(self, obj):
            return obj.get_urn()[1]

        def get_language(self, obj):
            if obj.language:
                return pycountry.languages.get(bibliographic=obj.language).name
            return None

        def get_last_response(self, obj):
            last_response = obj.responses.order_by('-updated_on').first()
            return last_response.updated_on if last_response else _("Never")

        def lookup_field_label(self, context, field, default=None):
            if field == 'urn':
                scheme = self.object.get_urn()[0]
                for s, label in URN_SCHEME_CHOICES:
                    if scheme == s:
                        return label

            return super(ContactCRUDL.Read, self).lookup_field_label(context, field, default)

    class List(OrgPermsMixin, ContactFieldsMixin, SmartListView):
        default_order = ('name',)
        search_fields = ('name__icontains', 'urn__icontains')

        def derive_fields(self):
            base_fields = ['name', 'urn', 'group']
            if self.request.region:
                return base_fields + self.derive_pollruns().keys()
            else:
                return base_fields + ['region']

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('pollrun_'):
                pollrun = self.derive_pollruns()[field]
                return "%s (%s)" % (pollrun.poll.name, pollrun.conducted_on.date())

            return super(ContactCRUDL.List, self).lookup_field_label(context, field, default)

        def lookup_field_value(self, context, obj, field):
            if field.startswith('pollrun_'):
                pollrun = self.derive_pollruns()[field]
                has_completed = pollrun.responses.filter(
                    contact=obj, status=RESPONSE_COMPLETE).exists()
                return ('<span class="glyphicon glyphicon-%s"></span>' %
                        ('ok' if has_completed else 'time'))

            return super(ContactCRUDL.List, self).lookup_field_value(context, obj, field)

        def lookup_field_class(self, field, obj=None, default=None):
            if field.startswith('pollrun_'):
                return 'centered'

            return super(ContactCRUDL.List, self).lookup_field_class(field, obj, default)

        def derive_pollruns(self):
            def fetch():
                pollruns = OrderedDict()
                qs = PollRun.get_all(self.request.org, self.request.region)
                qs = qs.order_by('-conducted_on')
                for pollrun in qs[0:3]:
                    pollruns['pollrun_%d' % pollrun.pk] = pollrun
                return pollruns

            return get_obj_cacheable(self, '_pollruns', fetch)

        def derive_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).derive_queryset(**kwargs)
            qs = qs.filter(org=self.request.org, is_active=True)

            if self.request.region:
                qs = qs.filter(region=self.request.region)

            return qs

    class Delete(OrgObjPermsMixin, SmartDeleteView):
        cancel_url = '@contacts.contact_list'

        def post(self, request, *args, **kwargs):
            self.object = self.get_object()

            if self.request.user.has_region_access(self.object.region):
                self.pre_delete(self.object)
                self.object.release()
                return HttpResponseRedirect(reverse('contacts.contact_list'))
            else:
                raise PermissionDenied()
