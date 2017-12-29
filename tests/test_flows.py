# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.messages.api import get_messages
from django.contrib.messages.storage.base import Message
from django.test import Client, override_settings

from allauth_cas.test.testcases import CASTestCase

User = get_user_model()


class LogoutFlowTests(CASTestCase):
    expected_msg_str = (
        "To logout of The Provider, please close your browser, or visit this "
        "<a href=\"/accounts/theid/logout/?next=%2Fredir%2F\">"
        "link</a>."
    )

    def setUp(self):
        self.client_cas_login(self.client)

    def assertCASLogoutNotInMessages(self, response):
        r_messages = get_messages(response.wsgi_request)
        self.assertNotIn(
            self.expected_msg_str,
            (str(msg) for msg in r_messages),
        )
        self.assertTemplateNotUsed(
            response,
            'socialaccount/messages/suggest_caslogout.html',
        )

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT': True,
            'MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT_LEVEL': messages.WARNING,
        },
    })
    def test_message_on_logout(self):
        """
        Message is sent to propose user to logout of CAS.
        """
        r = self.client.post('/accounts/logout/?next=/redir/')
        r_messages = get_messages(r.wsgi_request)

        expected_msg = Message(messages.WARNING, self.expected_msg_str)

        self.assertIn(expected_msg, r_messages)
        self.assertTemplateUsed(
            r, 'socialaccount/messages/suggest_caslogout.html')

    def test_message_on_logout_disabled(self):
        r = self.client.post('/accounts/logout/')
        self.assertCASLogoutNotInMessages(r)

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {'MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT': True},
    })
    def test_other_logout(self):
        """
        The CAS logout message doesn't appear with other login methods.
        """
        User.objects.create_user('user', '', 'user')
        client = Client()
        client.login(username='user', password='user')

        r = client.post('/accounts/logout/')
        self.assertCASLogoutNotInMessages(r)
