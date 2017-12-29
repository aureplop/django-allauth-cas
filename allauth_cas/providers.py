# -*- coding: utf-8 -*-
from six.moves.urllib.parse import parse_qsl

import django
from django.contrib import messages
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from allauth.socialaccount.providers.base import Provider

if django.VERSION >= (1, 10):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse


class CASProvider(Provider):

    def get_auth_params(self, request, action):
        settings = self.get_settings()
        ret = dict(settings.get('AUTH_PARAMS', {}))
        dynamic_auth_params = request.GET.get('auth_params')
        if dynamic_auth_params:
            ret.update(dict(parse_qsl(dynamic_auth_params)))
        return ret

    ##
    # Data extraction from CAS responses.
    ##

    def extract_uid(self, data):
        """Extract the user uid.

        Notes:
            Each pair ``(provider_id, uid)`` is unique and related to a single
            user.

        Args:
            data (uid (str), extra (dict)): CAS response. Example:
                ``('alice', {'name': 'Alice'})``

        Returns:
            str: Default to ``data[0]``, user identifier for the CAS server.

        """
        uid, _ = data
        return uid

    def extract_common_fields(self, data):
        """Extract the data to pass to `SOCIALACCOUNT_ADAPTER.populate_user()`.

        Args:
            data (uid (str), extra (dict)): CAS response. Example:
                ``('alice', {'name': 'Alice'})``

        Returns:
            dict: Default::

                {
                    'username': extra.get('username', uid),
                    'email': extra.get('email'),
                    'first_name': extra.get('first_name'),
                    'last_name': extra.get('last_name'),
                    'name': extra.get('name'),
                }

        """
        uid, extra = data
        return {
            'username': extra.get('username', uid),
            'email': extra.get('email'),
            'first_name': extra.get('first_name'),
            'last_name': extra.get('last_name'),
            'name': extra.get('name'),
        }

    def extract_email_addresses(self, data):
        """Extract the email addresses.

        Args:
            data (uid (str), extra (dict)): CAS response. Example:
                ``('alice', {'name': 'Alice'})``

        Returns:
            `list` of `EmailAddress`: By default, ``[]``.

            Example::

                [
                    EmailAddress(
                        email='user@domain.net',
                        verified=True, primary=True,
                    ),
                    EmailAddress(
                        email='alias@domain.net',
                        verified=True, primary=False,
                    ),
                ]

        """
        return super(CASProvider, self).extract_email_addresses(data)

    def extract_extra_data(self, data):
        """Extract the data to save to `SocialAccount.extra_data`.

        Args:
            data (uid (str), extra (dict)): CAS response. Example:
                ``('alice', {'name': 'Alice'})``

        Returns:
            dict: By default, ``data``.
        """
        uid, extra = data
        return dict(extra, uid=uid)

    ##
    # Message to suggest users to logout of the CAS server.
    ##

    def add_message_suggest_caslogout(
        self, request, next_page=None, level=None,
    ):
        """Add a message with a link for the user to logout of the CAS server.

        It uses the template ``socialaccount/messages/suggest_caslogout.html``,
        with the ``provider`` and the ``logout_url`` as context.

        Args:
            request: The request to which the message is added.
            next_page (optional): Added to the logout link for the CAS server
                to redirect the user to this url.
                Default: ``request.get_full_path()``
            level: The message level. Default: ``messages.INFO``

        """
        if next_page is None:
            next_page = request.get_full_path()
        if level is None:
            level = messages.INFO

        logout_url = self.get_logout_url(request, next=next_page)

        # DefaultAccountAdapter.add_message is unusable because it always
        # escape the message content.

        template = 'socialaccount/messages/suggest_caslogout.html'
        context = {
            'provider': self,
            'logout_url': logout_url,
        }

        messages.add_message(
            request, level,
            mark_safe(render_to_string(template, context).strip()),
            fail_silently=True,
        )

    def message_suggest_caslogout_on_logout(self, request):
        """Indicates whether the logout message should be sent on user logout.

        By default, it returns
        ``settings.SOCIALACCOUNT_PROVIDERS[self.id]['MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT']``
        or ``False``.

        Notes:
            The ``request`` argument is the one trigerring the emission of the
            signal ``user_logged_out``.

        """
        return (
            self.get_settings()
            .get('MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT', False)
        )

    def message_suggest_caslogout_on_logout_level(self, request):
        """Level of the logout message issued on user logout.

        By default, it returns
        ``settings.SOCIALACCOUNT_PROVIDERS[self.id]['MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT_LEVEL']``
        or ``messages.INFO``.

        Notes:
            The ``request`` argument is the one trigerring the emission of the
            signal ``user_logged_out``.

        """
        return (
            self.get_settings()
            .get('MESSAGE_SUGGEST_CASLOGOUT_ON_LOGOUT_LEVEL', messages.INFO)
        )

    ##
    # Shortcuts functions.
    ##

    def get_login_url(self, request, **kwargs):
        url = reverse(self.id + '_login')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url

    def get_callback_url(self, request, **kwargs):
        url = reverse(self.id + '_callback')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url

    def get_logout_url(self, request, **kwargs):
        url = reverse(self.id + '_logout')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url
