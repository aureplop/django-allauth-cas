# -*- coding: utf-8 -*-
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from django.test import TestCase as DjangoTestCase

from allauth_cas import CAS_PROVIDER_SESSION_KEY

from . import cas_clients


class TestCase(DjangoTestCase):

    def patch_cas_client(self, label):
        """
        Patch cas.CASClient in allauth_cs.views module with another CAS client
        selectable with label argument.

        Patch is stopped at the end of the current test.
        """
        if hasattr(self, '_patch_cas_client'):
            self.patch_cas_client_stop()

        if label == 'verify':
            new = cas_clients.VerifyCASClient
        elif label == 'accept':
            new = cas_clients.AcceptCASClient
        elif label == 'reject':
            new = cas_clients.RejectCASClient

        self._patch_cas_client = patch('allauth_cas.views.cas.CASClient', new)
        self._patch_cas_client.start()

    def patch_cas_client_stop(self):
        self._patch_cas_client.stop()

    def tearDown(self):
        if hasattr(self, '_patch_cas_client'):
            self.patch_cas_client_stop()


class CASViewTestCase(TestCase):

    def assertLoginSuccess(self, response, redirect_to=None, client=None):
        """
        Asserts response corresponds to a successful login.

        To check this, the response should redirect to redirect_to (default to
        /accounts/profile/, the default redirect after a successful login).
        Also CAS_PROVIDER_SESSION_KEY should be set in the client' session. By
        default, self.client is used.
        """
        if client is None:
            client = self.client
        if redirect_to is None:
            redirect_to = '/accounts/profile/'

        self.assertRedirects(
            response, redirect_to,
            fetch_redirect_response=False,
        )
        self.assertIn(
            CAS_PROVIDER_SESSION_KEY,
            client.session,
        )

    def assertLoginFailure(self, response):
        """
        Asserts response corresponds to a failed login.
        """
        return self.assertInHTML(
            '<h1>Social Network Login Failure</h1>',
            str(response.content),
        )
