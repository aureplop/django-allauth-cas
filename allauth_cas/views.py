# -*- coding: utf-8 -*-
import django
from django.http import HttpResponseRedirect
from django.utils.http import urlencode

from allauth.account.adapter import get_adapter
from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount import providers
from allauth.socialaccount.helpers import (
    complete_social_login, render_authentication_error,
)

import cas

from . import CAS_PROVIDER_SESSION_KEY
from .exceptions import CASAuthenticationError

if django.VERSION >= (1, 10):
    from django.urls import reverse
else:
    from django.core.urlresolvers import reverse


class AuthAction(object):
    AUTHENTICATE = 'authenticate'
    REAUTHENTICATE = 'reauthenticate'
    DEAUTHENTICATE = 'deauthenticate'


class CASAdapter(object):

    def __init__(self, request):
        self.request = request

    @property
    def renew(self):
        """
        If user is already authenticated on Django, he may already been
        connected to CAS, but still may want to use another CAS account.
        We set renew to True in this case, as the CAS server won't use the
        single sign-on.
        To specifically check, if the current user has used a CAS server,
        we check if the CAS session key is set.
        """
        return CAS_PROVIDER_SESSION_KEY in self.request.session

    def get_provider(self):
        """
        Returns a provider instance for the current request.
        """
        return providers.registry.by_id(self.provider_id, self.request)

    def complete_login(self, request, response):
        """
        Executed by the callback view after successful authentication on CAS
        server.

        Returns the SocialLogin object which represents the state of the
        current login-session.
        """
        login = (self.get_provider()
                 .sociallogin_from_response(request, response))
        return login

    def get_service_url(self, request):
        """
        Returns the service url to for a CAS client.

        From CAS specification, the service url is used in order to redirect
        user after a successful login on CAS server. Also, service_url sent
        when ticket is verified must be the one for which ticket was issued.

        To conform this, the service url is always the callback url.

        A redirect url is found from the current request and appended as
        parameter to the service url and is latter used by the callback view to
        redirect user.
        """
        redirect_to = get_next_redirect_url(request)

        callback_kwargs = {'next': redirect_to} if redirect_to else {}
        callback_url = self.get_callback_url(request, **callback_kwargs)

        service_url = request.build_absolute_uri(callback_url)

        return service_url

    def get_callback_url(self, request, **kwargs):
        """
        Returns the callback url of the provider.

        Keyword arguments are set as query string.
        """
        url = reverse(self.provider_id + '_callback')
        if kwargs:
            url += '?' + urlencode(kwargs)
        return url


class CASView(object):

    @classmethod
    def adapter_view(cls, adapter, **kwargs):
        """
        Similar to the Django as_view() method.

        It also setups a few things:
        - given adapter argument will be used in views internals.
        - if the view execution raises a CASAuthenticationError, the view
          renders an authentication error page.

        To use this:

        - subclass CAS adapter as wanted:

            class MyAdapter(CASAdapter):
                url = 'https://my.cas.url'

        - define views:

            login = views.CASLoginView.adapter_view(MyAdapter)
            callback = views.CASCallbackView.adapter_view(MyAdapter)
            logout = views.CASLogoutView.adapter_view(MyAdapter)

        """
        def view(request, *args, **kwargs):
            # Prepare the func-view.
            self = cls()

            self.request = request
            self.args = args
            self.kwargs = kwargs

            # Setup and store adapter as view attribute.
            self.adapter = adapter(request)

            try:
                return self.dispatch(request, *args, **kwargs)
            except CASAuthenticationError:
                return self.render_error()

        return view

    def get_client(self, request, action=AuthAction.AUTHENTICATE):
        """
        Returns the CAS client to interact with the CAS server.
        """
        provider = self.adapter.get_provider()
        auth_params = provider.get_auth_params(request, action)

        service_url = self.adapter.get_service_url(request)

        client = cas.CASClient(
            service_url=service_url,
            server_url=self.adapter.url,
            version=self.adapter.version,
            renew=self.adapter.renew,
            extra_login_params=auth_params,
        )

        return client

    def render_error(self):
        """
        Returns an HTTP response in case an authentication failure happens.
        """
        return render_authentication_error(
            self.request,
            self.adapter.provider_id,
        )


class CASLoginView(CASView):

    def dispatch(self, request):
        """
        Redirects to the CAS server login page.
        """
        action = request.GET.get('action', AuthAction.AUTHENTICATE)
        client = self.get_client(request, action=action)
        return HttpResponseRedirect(client.get_login_url())


class CASCallbackView(CASView):

    def dispatch(self, request):
        """
        The CAS server redirects the user to this view after a successful
        authentication.

        On redirect, CAS server should add a ticket whose validity is verified
        here. If ticket is valid, CAS server may also return extra attributes
        about user.
        """
        provider = self.adapter.get_provider()
        client = self.get_client(request)

        # CAS server should let a ticket.
        try:
            ticket = request.GET['ticket']
        except KeyError:
            raise CASAuthenticationError(
                "CAS server didn't respond with a ticket."
            )

        # Check ticket validity.
        # Response format on:
        # - success: username, attributes, pgtiou
        # - error: None, {}, None
        response = client.verify_ticket(ticket)

        if not response[0]:
            raise CASAuthenticationError(
                "CAS server doesn't validate the ticket."
            )

        # The CAS provider in use is stored to propose to the user to
        # disconnect from the latter when he logouts.
        request.session[CAS_PROVIDER_SESSION_KEY] = provider.id

        # Finish the login flow
        login = self.adapter.complete_login(request, response)
        return complete_social_login(request, login)


class CASLogoutView(CASView):

    def dispatch(self, request, next_page=None):
        """
        Redirects to the CAS server logout page.

        next_page is used to let the CAS server send back the user. If empty,
        the redirect url is built on request data.
        """
        action = AuthAction.DEAUTHENTICATE

        redirect_url = next_page or self.get_redirect_url()
        redirect_to = request.build_absolute_uri(redirect_url)

        client = self.get_client(request, action=action)

        return HttpResponseRedirect(client.get_logout_url(redirect_to))

    def get_redirect_url(self):
        """
        Returns the url to redirect after logout from current request.
        """
        request = self.request
        return (
            get_next_redirect_url(request) or
            get_adapter(request).get_logout_redirect_url(request)
        )
