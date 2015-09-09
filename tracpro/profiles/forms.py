from django import forms
from django.contrib.auth.models import User
from django.core.validators import MinLengthValidator
from django.utils.translation import ugettext_lazy as _

from tracpro.groups.fields import ModifiedLevelTreeNodeMultipleChoiceField
from tracpro.groups.models import Region


class UserForm(forms.ModelForm):

    full_name = forms.CharField(max_length=128, label=_("Full name"))
    is_active = forms.BooleanField(
        label=_("Active"),
        required=False,
        help_text=_("Whether this user is active. Disable to remove access."))
    email = forms.CharField(
        label=_("Email"),
        max_length=256,
        help_text=_("Email address and login."))
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput,
        validators=[MinLengthValidator(8)],
        help_text=_("Password used to log in (minimum of 8 characters)."))
    new_password = forms.CharField(
        label=_("New password"),
        required=False,
        widget=forms.PasswordInput,
        validators=[MinLengthValidator(8)],
        help_text=_("Password used to login (minimum of 8 characters, optional)."))
    confirm_password = forms.CharField(
        label=_("Confirm password"),
        required=False,
        widget=forms.PasswordInput)
    change_password = forms.BooleanField(
        label=_("Require change"),
        required=False,
        help_text=_("Whether user must change password on next login."))
    regions = ModifiedLevelTreeNodeMultipleChoiceField(
        label=_("Regions"),
        queryset=Region.objects.all(),
        required=False,
        help_text=_("Region(s) which this user can access. User will "
                    "automatically be granted access to sub-regions."))

    class Meta:
        model = User
        fields = forms.ALL_FIELDS

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        super(UserForm, self).__init__(*args, **kwargs)
        if self.user.get_org():
            regions = Region.get_all(self.user.get_org())
            self.fields['regions'].queryset = regions

    def clean(self):
        cleaned_data = super(UserForm, self).clean()
        password = cleaned_data.get('password', None) or cleaned_data.get('new_password', None)
        if password:
            confirm_password = cleaned_data.get('confirm_password', '')
            if password != confirm_password:
                self.add_error('confirm_password', _("Passwords don't match."))
