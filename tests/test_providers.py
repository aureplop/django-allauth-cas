# -*- coding: utf-8 -*-
from six.moves.urllib.parse import urlencode

from django.contrib import messages
from django.contrib.messages.api import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.base import Message
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase, override_settings

from allauth.socialaccount.providers import registry

from allauth_cas.views import AuthAction

from .example.provider import ExampleCASProvider


class CASProviderTests(TestCase):

    def setUp(self):
        self.request = self._get_request()
        self.provider = ExampleCASProvider(self.request)

    def _get_request(self):
        request = RequestFactory().get('/test/')
        SessionMiddleware().process_request(request)
        MessageMiddleware().process_request(request)
        return request

    def test_register(self):
        """
        Example CAS provider is registered as social account provider.
        """
        self.assertIsInstance(registry.by_id('theid'), ExampleCASProvider)

    def test_get_login_url(self):
        url = self.provider.get_login_url(self.request)
        self.assertEqual('/accounts/theid/login/', url)

        url_with_qs = self.provider.get_login_url(
            self.request,
            next='/path?quéry=string&two=whoam%C3%AF',
        )
        self.assertEqual(
            url_with_qs,
            '/accounts/theid/login/?next=%2Fpath%3Fqu%C3%A9ry%3Dstring%26two%3'
            'Dwhoam%25C3%25AF'
        )

    def test_get_callback_url(self):
        url = self.provider.get_callback_url(self.request)
        self.assertEqual('/accounts/theid/login/callback/', url)

        url_with_qs = self.provider.get_callback_url(
            self.request,
            next='/path?quéry=string&two=whoam%C3%AF',
        )
        self.assertEqual(
            url_with_qs,
            '/accounts/theid/login/callback/?next=%2Fpath%3Fqu%C3%A9ry%3Dstrin'
            'g%26two%3Dwhoam%25C3%25AF'
        )

    def test_get_logout_url(self):
        url = self.provider.get_logout_url(self.request)
        self.assertEqual('/accounts/theid/logout/', url)

        url_with_qs = self.provider.get_logout_url(
            self.request,
            next='/path?quéry=string&two=whoam%C3%AF',
        )
        self.assertEqual(
            url_with_qs,
            '/accounts/theid/logout/?next=%2Fpath%3Fqu%C3%A9ry%3Dstring%26two%'
            '3Dwhoam%25C3%25AF'
        )

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'AUTH_PARAMS': {'key': 'value'},
        },
    })
    def test_get_auth_params(self):
        action = AuthAction.AUTHENTICATE

        auth_params = self.provider.get_auth_params(self.request, action)

        self.assertDictEqual(auth_params, {
            'key': 'value',
        })

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'AUTH_PARAMS': {'key': 'value'},
        },
    })
    def test_get_auth_params_with_dynamic(self):
        factory = RequestFactory()
        request = factory.get(
            '/test/?auth_params=next%3Dtwo%253Dwhoam%2525C3%2525AF%2526qu%2525'
            'C3%2525A9ry%253Dstring'
        )
        request.session = {}

        action = AuthAction.AUTHENTICATE

        auth_params = self.provider.get_auth_params(request, action)

        self.assertDictEqual(auth_params, {
            'key': 'value',
            'next': 'two=whoam%C3%AF&qu%C3%A9ry=string',
        })

    def test_add_message_suggest_caslogout(self):
        expected_msg_base_str = (
            "To logout of The Provider, please close your browser, or visit "
            "this <a href=\"/accounts/theid/logout/?{}\">link</a>."
        )

        # Defaults.
        req1 = self.request

        self.provider.add_message_suggest_caslogout(req1)

        expected_msg1 = Message(
            messages.INFO,
            expected_msg_base_str.format(urlencode({'next': '/test/'})),
        )
        self.assertIn(expected_msg1, get_messages(req1))

        # Custom arguments.
        req2 = self._get_request()

        self.provider.add_message_suggest_caslogout(
            req2, next_page='/redir/', level=messages.WARNING)

        expected_msg2 = Message(
            messages.WARNING,
            expected_msg_base_str.format(urlencode({'next': '/redir/'})),
        )
        self.assertIn(expected_msg2, get_messages(req2))

    def test_message_suggest_caslogout_on_logout(self):
        self.assertFalse(
            self.provider.message_suggest_caslogout_on_logout(self.request))

        with override_settings(SOCIALACCOUNT_PROVIDERS={
            'theid': {'MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT': True},
        }):
            self.assertTrue(
                self.provider
                .message_suggest_caslogout_on_logout(self.request)
            )

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT_LEVEL': messages.WARNING,
        },
    })
    def test_message_suggest_caslogout_on_logout_level(self):
        self.assertEqual(messages.WARNING, (
            self.provider
            .message_suggest_caslogout_on_logout_level(self.request)
        ))

    def test_extract_uid(self):
        response = 'useRName', {}
        uid = self.provider.extract_uid(response)
        self.assertEqual('useRName', uid)

    def test_extract_common_fields(self):
        response = 'useRName', {}
        common_fields = self.provider.extract_common_fields(response)
        self.assertDictEqual(common_fields, {
            'username': 'useRName',
            'first_name': None,
            'last_name': None,
            'name': None,
            'email': None,
        })

    def test_extract_common_fields_with_extra(self):
        response = 'useRName', {'username': 'user', 'email': 'user@mail.net'}
        common_fields = self.provider.extract_common_fields(response)
        self.assertDictEqual(common_fields, {
            'username': 'user',
            'first_name': None,
            'last_name': None,
            'name': None,
            'email': 'user@mail.net',
        })

    def test_extract_extra_data(self):
        response = 'useRName', {'user_attr': 'thevalue', 'another': 'value'}
        extra_data = self.provider.extract_extra_data(response)
        self.assertDictEqual(extra_data, {
            'user_attr': 'thevalue',
            'another': 'value',
            'uid': 'useRName',
        })
