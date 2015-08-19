from __future__ import absolute_import, unicode_literals

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from tracpro.test.cases import TracProDataTest


class UserCRUDLTest(TracProDataTest):

    def test_create(self):
        url = reverse('profiles.user_create')

        # log in as an org administrator
        self.login(self.admin)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')
        self.assertFormError(response, 'form', 'password', 'This field is required.')

        # submit again with all required fields but invalid password
        data = dict(full_name="Mo Polls", email="mo@trac.com", password="123", confirm_password="123")
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', 'password', "Ensure this value has at least 8 characters (it has 3).")

        # submit again with valid password but mismatched confirmation
        data = dict(full_name="Mo Polls", email="mo@trac.com", password="Qwerty123", confirm_password="123")
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', 'confirm_password', "Passwords don't match.")

        # submit again with valid password and confirmation
        data = dict(full_name="Mo Polls", email="mo@trac.com", password="Qwerty123", confirm_password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check new user and profile
        user = User.objects.get(email="mo@trac.com")
        self.assertEqual(user.profile.full_name, "Mo Polls")
        self.assertEqual(user.email, "mo@trac.com")
        self.assertEqual(user.username, "mo@trac.com")

        # try again with same email address
        data = dict(full_name="Mo Polls II", email="mo@trac.com", password="Qwerty123", confirm_password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', None, "Email address already taken.")

    def test_update(self):
        url = reverse('profiles.user_update', args=[self.user1.pk])

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['form'].fields['regions'].choices), 3)  # can assign to any org region

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')

        # submit with all fields entered
        data = dict(full_name="Morris", email="mo2@chat.com", regions=[self.region3.pk], is_active=True)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check updated user and profile
        user = User.objects.get(pk=self.user1.pk)
        self.assertEqual(user.profile.full_name, "Morris")
        self.assertEqual(user.email, "mo2@chat.com")
        self.assertEqual(user.username, "mo2@chat.com")
        self.assertEqual(list(user.regions.all()), [self.region3])

        # submit again for good measure
        data = dict(full_name="Morris", email="mo2@chat.com", regions=[self.region3.pk], is_active=True)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # try giving user someone else's email address
        data = dict(full_name="Morris", email="eric@nyaruka.com", password="Qwerty123", confirm_password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertFormError(response, 'form', None, "Email address already taken.")

        # check de-activating user
        data = dict(full_name="Morris", email="mo2@chat.com", regions=[], is_active=False)
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check user object is inactive
        user = User.objects.get(pk=self.user1.pk)
        self.assertFalse(user.is_active)

    def test_read(self):
        # log in as an org administrator
        self.login(self.admin)

        # view our own profile
        response = self.url_get('unicef', reverse('profiles.user_read', args=[self.admin.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('profiles.user_self'))

        # view other user's profile
        response = self.url_get('unicef', reverse('profiles.user_read', args=[self.user1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['edit_button_url'], reverse('profiles.user_update', args=[self.user1.pk]))

        # try to view user from other org
        response = self.url_get('unicef', reverse('profiles.user_read', args=[self.user3.pk]))
        self.assertEqual(response.status_code, 404)

        # log in as a user
        self.login(self.user1)

        # view other user's profile
        response = self.url_get('unicef', reverse('profiles.user_read', args=[self.admin.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['edit_button_url'])

    def test_list(self):
        url = reverse('profiles.user_list')

        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

        # log in as a non-administrator
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['object_list']), 2)

    def test_self(self):
        url = reverse('profiles.user_self')

        # try as unauthenticated
        response = self.url_get('unicef', url)
        self.assertLoginRedirect(response, 'unicef', url)

        # try as superuser (doesn't have a chat profile)
        self.login(self.superuser)
        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 404)

        # log in as an org administrator
        self.login(self.admin)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # log in as a user
        self.login(self.user1)

        response = self.url_get('unicef', url)
        self.assertEqual(response.status_code, 200)

        # submit with no fields entered
        response = self.url_post('unicef', url, dict())
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'full_name', 'This field is required.')
        self.assertFormError(response, 'form', 'email', 'This field is required.')

        # submit with all required fields entered
        data = dict(full_name="Morris", email="mo2@trac.com")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check updated user and profile
        user = User.objects.get(pk=self.user1.pk)
        self.assertEqual(user.profile.full_name, "Morris")
        self.assertEqual(user.email, "mo2@trac.com")
        self.assertEqual(user.username, "mo2@trac.com")
        self.assertEqual(list(user.regions.all()), [self.region1])

        # submit with all required fields entered and password fields
        old_password_hash = user.password
        data = dict(full_name="Morris", email="mo2@trac.com", new_password="Qwerty123", confirm_password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check password has been changed
        user = User.objects.get(pk=self.user1.pk)
        self.assertNotEqual(user.password, old_password_hash)

        # check when user is being forced to change their password
        old_password_hash = user.password
        self.user1.profile.change_password = True
        self.user1.profile.save()

        # submit without password
        data = dict(full_name="Morris", email="mo2@trac.com")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'password', 'This field is required.')

        # submit again with password but no confirmation
        data = dict(full_name="Morris", email="mo2@trac.com", password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response, 'form', 'confirm_password', "Passwords don't match.")

        # submit again with password and confirmation
        data = dict(full_name="Morris", email="mo2@trac.com", password="Qwerty123", confirm_password="Qwerty123")
        response = self.url_post('unicef', url, data)
        self.assertEqual(response.status_code, 302)

        # check password has changed and no longer has to be changed
        user = User.objects.get(pk=self.user1.pk)
        self.assertFalse(user.profile.change_password)
        self.assertNotEqual(user.password, old_password_hash)


class DashUserCRUDLTest(TracProDataTest):

    def test_login(self):
        url = reverse('users.user_login')

        # login without org subdomain
        response = self.url_post(None, url, dict(username='sam@unicef.org', password='sam@unicef.org'))
        self.assertRedirects(response, 'http://testserver/', fetch_redirect_response=False)

        # login with org subdomain
        response = self.url_post('unicef', url, dict(username='sam@unicef.org', password='sam@unicef.org'))
        self.assertRedirects(response, 'http://unicef.testserver/', fetch_redirect_response=False)
