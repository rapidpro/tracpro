from __future__ import absolute_import, unicode_literals

import pycountry

from collections import OrderedDict
from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils import get_obj_cacheable
from dash.utils.sync import ChangeType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django import forms
from django.http import HttpResponseRedirect, JsonResponse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartListView, SmartCreateView, SmartReadView, SmartUpdateView, SmartDeleteView
from smartmin.users.views import SmartCRUDL
from tracpro.groups.models import Region, Group
from tracpro.polls.models import Issue, RESPONSE_COMPLETE
from .models import Contact


URN_SCHEME_TEL = 'tel'
URN_SCHEME_TWITTER = 'twitter'
URN_SCHEME_CHOICES = ((URN_SCHEME_TEL, _("Phone")), (URN_SCHEME_TWITTER, _("Twitter")))


class URNField(forms.fields.MultiValueField):
    def __init__(self, *args, **kwargs):
        fields = (forms.ChoiceField(choices=URN_SCHEME_CHOICES),
                  forms.CharField(max_length=32))
        super(URNField, self).__init__(fields, *args, **kwargs)

        self.widget = URNWidget(scheme_choices=URN_SCHEME_CHOICES)

    def compress(self, values):
        return '%s:%s' % (values[0], values[1])


class URNWidget(forms.widgets.MultiWidget):
    def __init__(self, *args, **kwargs):
        scheme_choices = kwargs.pop('scheme_choices')

        widgets = (forms.Select(choices=scheme_choices),
                   forms.TextInput(attrs={'maxlength': 32}))
        super(URNWidget, self).__init__(widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split(':', 1)
        else:
            return URN_SCHEME_TEL, ''

    def render(self, name, value, attrs=None):
        output = ['<div class="urn-widget">',
                  super(URNWidget, self).render(name, value, attrs),
                  '</div>']
        return mark_safe(''.join(output))


class ContactForm(forms.ModelForm):
    """
    Form for contacts
    """
    name = forms.CharField(max_length=128, label=_("Full name"))

    urn = URNField(label=_("Phone/Twitter"), help_text=_("Phone number or Twitter handle of this contact."))

    region = forms.ModelChoiceField(label=_("Region"), queryset=Region.objects.filter(pk=-1),
                                    help_text=_("Region where this contact lives."))

    group = forms.ModelChoiceField(label=_("Reporter Group"), queryset=Group.objects.filter(pk=-1),
                                   help_text=_("Reporter Group to which this contact belongs."))

    facility_code = forms.CharField(max_length=16, label=_("Facility Code"), required=False)

    language = forms.CharField(label=_("Language"), required=False,
                               widget=forms.TextInput(attrs={'class': 'language-field'}))

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        org = self.user.get_org()

        super(ContactForm, self).__init__(*args, **kwargs)

        self.fields['region'].queryset = self.user.get_regions(org).order_by('name')
        self.fields['group'].queryset = Group.get_all(org).order_by('name')

    class Meta:
        model = Contact
        exclude = ()


class ContactFormMixin(object):
    """
    Mixin for views that use a contact form
    """
    def get_form_kwargs(self):
        kwargs = super(ContactFormMixin, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get(self, request, *args, **kwargs):
        if 'initial' in self.request.REQUEST:
            initial = self.request.REQUEST['initial']
            results = []
            if initial:
                lang = pycountry.languages.get(bibliographic=initial)
                name = lang.name.split(';')[0]
                results.append(dict(id=lang.bibliographic, text=name))
            return JsonResponse(dict(results=results))

        if 'search' in self.request.REQUEST:
            search = self.request.REQUEST['search'].strip().lower()
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
            regions = self.request.user.get_regions(self.request.org)
            queryset = super(ContactCRUDL.Update, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True, region__in=regions)

        def post_save(self, obj):
            obj = super(ContactCRUDL.Update, self).post_save(obj)
            obj.push(ChangeType.updated)
            return obj

    class Read(OrgObjPermsMixin, SmartReadView):
        def derive_fields(self):
            fields = ['urn', 'region', 'group', 'facility_code', 'language', 'last_response']
            if self.object.created_by_id:
                fields.append('created_by')
            return fields

        def get_queryset(self):
            regions = self.request.user.get_regions(self.request.org)
            queryset = super(ContactCRUDL.Read, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True, region__in=regions)

        def get_urn(self, obj):
            return obj.get_urn()[1]

        def get_language(self, obj):
            return pycountry.languages.get(bibliographic=obj.language).name if obj.language else None

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
                return base_fields + self.derive_issues().keys()
            else:
                return base_fields + ['region']

        def lookup_field_label(self, context, field, default=None):
            if field.startswith('issue_'):
                issue = self.derive_issues()[field]
                return "%s (%s)" % (issue.poll.name, issue.conducted_on.date())

            return super(ContactCRUDL.List, self).lookup_field_label(context, field, default)

        def lookup_field_value(self, context, obj, field):
            if field.startswith('issue_'):
                issue = self.derive_issues()[field]
                has_completed = issue.responses.filter(contact=obj, status=RESPONSE_COMPLETE).exists()
                return '<span class="glyphicon glyphicon-%s"></span>' % ('ok' if has_completed else 'time')

            return super(ContactCRUDL.List, self).lookup_field_value(context, obj, field)

        def lookup_field_class(self, field, obj=None, default=None):
            if field.startswith('issue_'):
                return 'centered'

            return super(ContactCRUDL.List, self).lookup_field_class(field, obj, default)

        def derive_issues(self):
            def fetch():
                issues = OrderedDict()
                for issue in Issue.get_all(self.request.org, self.request.region).order_by('-conducted_on')[0:3]:
                    issues['issue_%d' % issue.pk] = issue
                return issues

            return get_obj_cacheable(self, '_issues', fetch)

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
