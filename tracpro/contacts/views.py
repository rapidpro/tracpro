from __future__ import absolute_import, unicode_literals

from dash.orgs.views import OrgPermsMixin, OrgObjPermsMixin
from dash.utils.temba import ChangeType
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django import forms
from django.http import Http404, HttpResponseRedirect
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from smartmin.users.views import SmartListView, SmartCreateView, SmartReadView, SmartUpdateView, SmartDeleteView
from smartmin.users.views import SmartCRUDL
from tracpro.groups.models import Region, Group
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
    actions = ('create', 'update', 'read', 'list', 'filter', 'delete')

    class Create(OrgPermsMixin, ContactFormMixin, SmartCreateView):
        fields = ('name', 'urn', 'region', 'group')
        form_class = ContactForm

        def dispatch(self, request, *args, **kwargs):
            return super(ContactCRUDL.Create, self).dispatch(request, *args, **kwargs)

        def derive_initial(self):
            initial = super(ContactCRUDL.Create, self).derive_initial()
            region_id = self.kwargs.get('region', None)
            if region_id:
                initial['region'] = Region.objects.get(org=self.request.org, pk=region_id)
            return initial

        def save(self, obj):
            org = self.request.user.get_org()
            self.object = Contact.create(org, self.request.user, obj.name, obj.urn, obj.region, obj.group)

    class Update(OrgObjPermsMixin, ContactFormMixin, SmartUpdateView):
        fields = ('name', 'urn', 'region', 'group')
        form_class = ContactForm

        def dispatch(self, request, *args, **kwargs):
            return super(ContactCRUDL.Update, self).dispatch(request, *args, **kwargs)

        def post_save(self, obj):
            obj = super(ContactCRUDL.Update, self).post_save(obj)
            obj.push(ChangeType.updated)
            return obj

    class Read(OrgPermsMixin, SmartReadView):
        def derive_fields(self):
            fields = ['name', 'urn', 'region', 'group']
            if self.object.created_by_id:
                fields += ['added_by']
            return fields

        def get_queryset(self):
            queryset = super(ContactCRUDL.Read, self).get_queryset()
            return queryset.filter(org=self.request.org, is_active=True)

        def get_context_data(self, **kwargs):
            context = super(ContactCRUDL.Read, self).get_context_data(**kwargs)
            edit_button_url = None
            delete_button_url = None

            region = self.object.region
            if self.request.user.has_region_access(region):
                if self.has_org_perm('contacts.contact_update'):
                    edit_button_url = reverse('contacts.contact_update', args=[self.object.pk])
                if self.has_org_perm('contacts.contact_delete'):
                    delete_button_url = reverse('contacts.contact_delete', args=[self.object.pk])

            context['edit_button_url'] = edit_button_url
            context['delete_button_url'] = delete_button_url
            return context

        def get_urn(self, obj):
            return obj.get_urn()[1]

        def get_added_by(self, obj):
            return obj.created_by.get_full_name()

        def lookup_field_label(self, context, field, default=None):
            if field == 'urn':
                scheme = self.object.get_urn()[0]
                for s, label in URN_SCHEME_CHOICES:
                    if scheme == s:
                        return label

            return super(ContactCRUDL.Read, self).lookup_field_label(context, field, default)

    class List(OrgPermsMixin, ContactFieldsMixin, SmartListView):
        fields = ('name', 'urn', 'region', 'group')

        def get_queryset(self, **kwargs):
            qs = super(ContactCRUDL.List, self).get_queryset(**kwargs)

            regions = self.request.user.get_regions(self.request.org)
            qs = qs.filter(org=self.request.org, is_active=True, region__in=regions)
            return qs.order_by('name')

    class Filter(OrgPermsMixin, ContactFieldsMixin, SmartListView):
        fields = ('name', 'urn', 'group')

        @classmethod
        def derive_url_pattern(cls, path, action):
            return r'^%s/%s/(?P<region>\d+)/$' % (path, action)

        def derive_title(self):
            return _("Contacts in %s") % self.derive_region().name

        def derive_region(self):
            if hasattr(self, '_region'):
                return self._region

            region = Region.objects.filter(pk=self.kwargs['region'], org=self.request.org).first()
            if not region:
                raise Http404("No such region in this org")

            if region not in self.request.user.get_regions(self.request.org):
                raise PermissionDenied()

            self._region = region
            return region

        def get_queryset(self, **kwargs):
            return self.derive_region().get_contacts().order_by('name')

        def get_context_data(self, **kwargs):
            context = super(ContactCRUDL.Filter, self).get_context_data(**kwargs)
            context['region'] = self.derive_region()
            return context

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