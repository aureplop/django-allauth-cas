# -*- coding: utf-8 -*-
from six.moves.urllib.parse import parse_qsl

import django
from django.contrib import messages
from django.utils.http import urlencode

from allauth.socialaccount.providers.base import Provider

if django.VERSION >= (1, 10):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse


class CASProvider(Provider):

    def get_login_url(self, request, **kwargs):
        url = reverse(self.id + '_login')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url

    def get_logout_url(self, request, **kwargs):
        url = reverse(self.id + '_logout')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url

    def get_auth_params(self, request, action):
        settings = self.get_settings()
        ret = dict(settings.get('AUTH_PARAMS', {}))
        dynamic_auth_params = request.GET.get('auth_params')
        if dynamic_auth_params:
            ret.update(dict(parse_qsl(dynamic_auth_params)))
        return ret

    def message_on_logout(self, request):
        return self.get_settings().get('MESSAGE_ON_LOGOUT', True)

    def message_on_logout_level(self, request):
        return self.get_settings().get('MESSAGE_ON_LOGOUT_LEVEL',
                                       messages.INFO)

    def extract_uid(self, data):
        username, _, _ = data
        return username

    def extract_common_fields(self, data):
        username, _, _ = data
        return {'username': username}

    def extract_extra_data(self, data):
        _, extra_data, _ = data
        return extra_data
