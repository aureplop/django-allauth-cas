# -*- coding: utf-8 -*-
from django.test import Client, RequestFactory

from allauth_cas.test.testcases import CASViewTestCase
from allauth_cas.views import CASView

from .example.views import ExampleCASAdapter


class CASTestCaseTests(CASViewTestCase):

    def setUp(self):
        self.client.get('/accounts/theid/login/')

    def test_patch_cas_response_client_version(self):
        """
        python-cas uses multiple client classes depending on the CAS server
        version.

        patch_cas_response patch must also returns the correct class.

        """
        valid_versions = [
            1, '1',
            2, '2',
            3, '3',
            'CAS_2_SAML_1_0',
        ]
        invalid_versions = [
            'not_supported',
        ]

        factory = RequestFactory()
        request = factory.get('/path/')
        request.session = {}

        for _version in valid_versions + invalid_versions:
            class BasicCASAdapter(ExampleCASAdapter):
                version = _version

            class BasicCASView(CASView):
                def dispatch(self, request, *args, **kwargs):
                    return self.get_client(request)

            view = BasicCASView.adapter_view(BasicCASAdapter)

            if _version in valid_versions:
                raw_client = view(request)

                self.patch_cas_response(valid_ticket='__all__')
                mocked_client = view(request)

                self.assertEqual(type(raw_client), type(mocked_client))
            else:
                # This is a sanity check.
                self.assertRaises(ValueError, view, request)

                self.patch_cas_response(valid_ticket='__all__')
                self.assertRaises(ValueError, view, request)

    def test_patch_cas_response_verify_success(self):
        self.patch_cas_response(valid_ticket='123456')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '123456',
        })
        self.assertLoginSuccess(r)

    def test_patch_cas_response_verify_failure(self):
        self.patch_cas_response(valid_ticket='123456')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginFailure(r)

    def test_patch_cas_response_accept(self):
        self.patch_cas_response(valid_ticket='__all__')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginSuccess(r)

    def test_patch_cas_response_reject(self):
        self.patch_cas_response(valid_ticket=None)
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginFailure(r)

    def test_patch_cas_reponse_multiple(self):
        self.patch_cas_response(valid_ticket='__all__')
        client_0 = Client()
        client_0.get('/accounts/theid/login/')
        r_0 = client_0.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginSuccess(r_0)

        self.patch_cas_response(valid_ticket=None)
        client_1 = Client()
        client_1.get('/accounts/theid/login/')
        r_1 = client_1.get('/accounts/theid/login/callback/', {
            'ticket': '111111',
        })
        self.assertLoginFailure(r_1)

    def test_assertLoginSuccess(self):
        self.patch_cas_response(valid_ticket='__all__')
        r = self.client.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
            'next': '/path/',
        })
        self.assertLoginSuccess(r, redirect_to='/path/')
