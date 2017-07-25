# -*- coding: utf-8 -*-
from django.contrib import messages
from django.test import RequestFactory, TestCase, override_settings

from allauth.socialaccount.providers import registry

from allauth_cas.views import AuthAction

from .example.provider import ExampleCASProvider


class CASProviderTests(TestCase):

    def setUp(self):
        factory = RequestFactory()
        request = factory.get('/test/')
        request.session = {}
        self.request = request

        self.provider = ExampleCASProvider(request)

    def test_register(self):
        """
        Example CAS provider is registered as social account provider.
        """
        self.assertIsInstance(registry.by_id('theid'), ExampleCASProvider)

    def test_get_login_url(self):
        """
        get_login_url returns the url to logout of the provider.
        Keyword arguments are set as query string.
        """
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

    def test_get_logout_url(self):
        """
        get_logout_url returns the url to logout of the provider.
        Keyword arguments are set as query string.
        """
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

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'MESSAGE_ON_LOGOUT_LEVEL': messages.WARNING,
        },
    })
    def test_message_on_logout(self):
        message_on_logout = self.provider.message_on_logout(self.request)
        self.assertTrue(message_on_logout)

        message_level = self.provider.message_on_logout_level(self.request)
        self.assertEqual(messages.WARNING, message_level)

    def test_extract_uid(self):
        response = 'useRName', {}, None
        uid = self.provider.extract_uid(response)
        self.assertEqual('useRName', uid)

    def test_extract_common_fields(self):
        response = 'useRName', {}, None
        common_fields = self.provider.extract_common_fields(response)
        self.assertDictEqual(common_fields, {
            'username': 'useRName',
        })

    def test_extract_extra_data(self):
        attributes = {'user_attr': 'thevalue', 'another': 'value'}
        response = 'useRName', attributes, None
        extra_data = self.provider.extract_extra_data(response)
        self.assertDictEqual(extra_data, {
            'user_attr': 'thevalue',
            'another': 'value',
        })
