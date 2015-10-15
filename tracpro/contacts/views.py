from __future__ import absolute_import, unicode_literals

from collections import OrderedDict

import pycountry

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import get_obj_cacheable
from dash.utils.sync import ChangeType

from django.http import JsonResponse
from django.utils.translation import ugettext_lazy as _

from smartmin.users.views import (
    SmartListView, SmartCreateView, SmartReadView, SmartUpdateView,
    SmartDeleteView, SmartCRUDL)

from tracpro.polls.models import PollRun, Response

from .fields import URN_SCHEME_CHOICES
from .forms import ContactForm
from .models import Contact


class ContactCRUDL(SmartCRUDL):
    model = Contact
    actions = ('create', 'read', 'update', 'delete', 'list')

    class ContactBase(object):

        def get_queryset(self):
            regions = self.request.user.get_all_regions(self.request.org)
            qs = super(ContactCRUDL.ContactBase, self).get_queryset()
            qs = qs.by_org(self.request.org).by_regions(regions).active()
            return qs

    class ContactFormMixin(object):

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

            return super(ContactCRUDL.ContactFormMixin, self).get(request, *args, **kwargs)

        def get_form_kwargs(self):
            kwargs = super(ContactCRUDL.ContactFormMixin, self).get_form_kwargs()
            kwargs['user'] = self.request.user
            return kwargs

    class ContactFieldsMixin(object):

        def get_language(self, obj):
            if obj.language:
                return pycountry.languages.get(bibliographic=obj.language).name
            return None

        def get_urn(self, obj):
            return obj.get_urn()[1]  # TODO indicate different urn types with icon?

    class Create(OrgPermsMixin, ContactFormMixin, ContactBase, SmartCreateView):
        form_class = ContactForm

        def derive_initial(self):
            initial = super(ContactCRUDL.Create, self).derive_initial()
            initial['region'] = self.request.region
            return initial

        def post_save(self, obj):
            obj = super(ContactCRUDL.Create, self).post_save(obj)
            obj.push(ChangeType.created)
            return obj

    class Update(OrgObjPermsMixin, ContactFormMixin, ContactBase, SmartUpdateView):
        form_class = ContactForm

        def post_save(self, obj):
            obj = super(ContactCRUDL.Update, self).post_save(obj)
            obj.push(ChangeType.updated)
            return obj

    class Read(OrgObjPermsMixin, ContactFieldsMixin, ContactBase, SmartReadView):

        def derive_fields(self):
            fields = ['urn', 'region', 'group', 'language', 'last_response']
            if self.object.created_by_id:
                fields.append('created_by')

            return fields

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

    class List(OrgPermsMixin, ContactFieldsMixin, ContactBase, SmartListView):
        default_order = ('name',)
        search_fields = ('name__icontains', 'urn__icontains')

        def derive_fields(self):
            fields = ['name', 'urn', 'group', 'region']
            if self.request.region:
                fields.extend(self.derive_pollruns().keys())
            return fields

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('pollrun_'):
                pollrun = self.derive_pollruns()[field]
                return "%s (%s)" % (pollrun.poll.name, pollrun.conducted_on.date())

            return super(ContactCRUDL.List, self).lookup_field_label(context, field, default)

        def lookup_field_value(self, context, obj, field):
            if field.startswith('pollrun_'):
                pollrun = self.derive_pollruns()[field]
                has_completed = pollrun.responses.filter(
                    contact=obj, status=Response.STATUS_COMPLETE).exists()
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
                qs = PollRun.objects.get_all(
                    self.request.org,
                    self.request.region,
                    self.request.include_subregions)
                qs = qs.order_by('-conducted_on')
                for pollrun in qs[0:3]:
                    pollruns['pollrun_%d' % pollrun.pk] = pollrun
                return pollruns

            return get_obj_cacheable(self, '_pollruns', fetch)

        def derive_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).derive_queryset(**kwargs)
            qs = qs.filter(org=self.request.org, is_active=True)
            if self.request.data_regions is not None:
                qs = qs.filter(region__in=self.request.data_regions)
            return qs

    class Delete(OrgObjPermsMixin, ContactBase, SmartDeleteView):
        cancel_url = '@contacts.contact_list'
        redirect_url = '@contacts.contact_list'
