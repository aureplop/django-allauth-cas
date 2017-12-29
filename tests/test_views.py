# -*- coding: utf-8 -*-
try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

import django
from django.test import RequestFactory, override_settings

from allauth_cas.exceptions import CASAuthenticationError
from allauth_cas.test.testcases import CASTestCase, CASViewTestCase
from allauth_cas.views import CASView

from .example.views import ExampleCASAdapter

if django.VERSION >= (1, 10):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse


class CASAdapterTests(CASTestCase):

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/path/')
        self.request.session = {}
        self.adapter = ExampleCASAdapter(self.request)

    def test_get_service_url(self):
        """
        Service url (used by CAS client) is the callback url.
        """
        expected = 'http://testserver/accounts/theid/login/callback/'
        service_url = self.adapter.get_service_url(self.request)
        self.assertEqual(expected, service_url)

    def test_get_service_url_keep_next(self):
        """
        Current GET paramater next is appended on service url.
        """
        expected = (
            'http://testserver/accounts/theid/login/callback/?next=%2Fnext%2F'
        )
        factory = RequestFactory()
        request = factory.get('/path/', {'next': '/next/'})
        adapter = ExampleCASAdapter(request)
        service_url = adapter.get_service_url(request)
        self.assertEqual(expected, service_url)

    def test_renew(self):
        """
        From an anonymous request, renew is False to let using the single
        sign-on.
        """
        self.assertFalse(self.adapter.renew)

    def test_renew_authenticated(self):
        """
        If user has been authenticated to the application through CAS, and
        tries to reauthenticate, renew is set to True to opt-out the single
        sign-on.
        """
        r = self.client_cas_login(self.client)
        adapter = ExampleCASAdapter(r.wsgi_request)
        self.assertTrue(adapter.renew)


class CASViewTests(CASViewTestCase):

    class BasicCASView(CASView):
        def dispatch(self, request, *args, **kwargs):
            return self

    def setUp(self):
        factory = RequestFactory()
        self.request = factory.get('/path/')
        self.request.session = {}

        self.cas_view = self.BasicCASView.adapter_view(ExampleCASAdapter)

    def test_adapter_view(self):
        """
        adapter_view prepares the func view from a class view.
        """
        view = self.cas_view(
            self.request,
            'arg1', 'arg2',
            kwarg1='kwarg1', kwarg2='kwarg2',
        )

        self.assertIsInstance(view, CASView)

        self.assertEqual(view.request, self.request)
        self.assertTupleEqual(view.args, ('arg1', 'arg2'))
        self.assertDictEqual(view.kwargs, {
            'kwarg1': 'kwarg1',
            'kwarg2': 'kwarg2',
        })

        self.assertIsInstance(view.adapter, ExampleCASAdapter)

    @patch('allauth_cas.views.cas.CASClient')
    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'theid': {
            'AUTH_PARAMS': {'key': 'value'},
        },
    })
    def test_get_client(self, mock_casclient_class):
        """
        get_client returns a CAS client, configured from settings.
        """
        view = self.cas_view(self.request)
        view.get_client(self.request)

        mock_casclient_class.assert_called_once_with(
            service_url='http://testserver/accounts/theid/login/callback/',
            server_url='https://server.cas',
            version=2,
            renew=False,
            extra_login_params={'key': 'value'},
        )

    def test_render_error_on_failure(self):
        """
        A common login failure page is rendered if CASAuthenticationError is
        raised by dispatch.
        """
        def dispatch_raise(self, request):
            raise CASAuthenticationError("failure")

        with patch.object(self.BasicCASView, 'dispatch', dispatch_raise):
            resp = self.cas_view(self.request)
            self.assertLoginFailure(resp)


class CASLoginViewTests(CASViewTestCase):

    def test_reverse(self):
        """
        Login view name is "{provider_id}_login".
        """
        url = reverse('theid_login')
        self.assertEqual('/accounts/theid/login/', url)

    def test_execute(self):
        """
        Login view redirects to the CAS server login url.
        Service is the callback url, as absolute uri.
        """
        r = self.client.get('/accounts/theid/login/')

        expected = (
            'https://server.cas/login?service=http%3A%2F%2Ftestserver%2F'
            'accounts%2Ftheid%2Flogin%2Fcallback%2F'
        )

        self.assertRedirects(r, expected, fetch_redirect_response=False)

    def test_execute_keep_next(self):
        """
        Current GET parameter 'next' is kept on service url.
        """
        r = self.client.get('/accounts/theid/login/?next=/path/')

        expected = (
            'https://server.cas/login?service=http%3A%2F%2Ftestserver%2F'
            'accounts%2Ftheid%2Flogin%2Fcallback%2F%3Fnext%3D%252Fpath%252F'
        )

        self.assertRedirects(r, expected, fetch_redirect_response=False)


class CASCallbackViewTests(CASViewTestCase):

    def setUp(self):
        self.client.get('/accounts/theid/login/')

    def test_reverse(self):
        """
        Callback view name is "{provider_id}_callback".
        """
        url = reverse('theid_callback')
        self.assertEqual('/accounts/theid/login/callback/', url)

    def test_ticket_valid(self):
        """p(
        If ticket is valid, the user is logged in.
        """
        self.patch_cas_response(username='username', valid_ticket='123456')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '123456',
        })
        self.assertLoginSuccess(r)

    def test_ticket_invalid(self):
        """
        Login failure page is returned if the ticket is invalid.
        """
        self.patch_cas_response(username='username', valid_ticket='123456')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginFailure(r)

    def test_ticket_missing(self):
        """
        Login failure page is returned if request lacks a ticket.
        """
        self.patch_cas_response(username='username', valid_ticket='123456')
        r = self.client.get('/accounts/theid/login/callback/')
        self.assertLoginFailure(r)


class CASLogoutViewTests(CASViewTestCase):

    def test_reverse(self):
        """
        Callback view name is "{provider_id}_logout".
        """
        url = reverse('theid_logout')
        self.assertEqual('/accounts/theid/logout/', url)

    def test_execute(self):
        """
        Logout view redirects to the CAS server logout url.
        Service is a url to here, as absolute uri.
        """
        r = self.client.get('/accounts/theid/logout/')

        expected = 'https://server.cas/logout?url=http%3A%2F%2Ftestserver%2F'

        self.assertRedirects(r, expected, fetch_redirect_response=False)

    def test_execute_with_next(self):
        """
        GET parameter 'next' is set as service url.
        """
        r = self.client.get('/accounts/theid/logout/?next=/path/')

        expected = (
            'https://server.cas/logout?url=http%3A%2F%2Ftestserver%2Fpath%2F'
        )

        self.assertRedirects(r, expected, fetch_redirect_response=False)
