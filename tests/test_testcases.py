# -*- coding: utf-8 -*-
from django.test import Client

from allauth_cas.test.testcases import CASViewTestCase


class CASTestCaseTests(CASViewTestCase):

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
        r_0 = client_0.get('/accounts/theid/login/callback/', {
            'ticket': '000000',
        })
        self.assertLoginSuccess(r_0)

        self.patch_cas_response(valid_ticket=None)
        client_1 = Client()
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
