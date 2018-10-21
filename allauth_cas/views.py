# -*- coding: utf-8 -*-
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property

from allauth.account.adapter import get_adapter
from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount import providers
from allauth.socialaccount.helpers import (
    complete_social_login, render_authentication_error,
)
from allauth.socialaccount.models import SocialLogin

import cas

from . import CAS_PROVIDER_SESSION_KEY
from .exceptions import CASAuthenticationError


class AuthAction(object):
    AUTHENTICATE = 'authenticate'
    REAUTHENTICATE = 'reauthenticate'
    DEAUTHENTICATE = 'deauthenticate'


class CASAdapter(object):
    #: CAS server url.
    url = None
    #: CAS server version.
    #: Choices: ``1`` or ``'1'``, ``2`` or ``'2'``, ``3`` or ``'3'``,
    #: ``'CAS_2_SAML_1_0'``
    version = None

    def __init__(self, request):
        self.request = request

    @cached_property
    def renew(self):
        """Controls presence of ``renew`` in requests to the CAS server.

        If ``True``, opt out single sign-on (SSO) functionality of the CAS
        server. So that, user is always prompted for his username and password.

        If ``False``, the CAS server does not prompt users for their
        credentials if a SSO exists.

        The default allows user to connect via an already used CAS server
        with other credentials.

        Returns:
            ``True`` if logged in user has already connected to Django using
            **any** CAS provider in the current session, ``False`` otherwise.

        """
        return CAS_PROVIDER_SESSION_KEY in self.request.session

    @cached_property
    def provider(self):
        """
        Returns a provider instance for the current request.
        """
        return providers.registry.by_id(self.provider_id, self.request)

    def complete_login(self, request, response):
        """
        Executed by the callback view after successful authentication on the
        CAS server.

        Args:
            request
            response (`dict`): Data returned by the CAS server.
                ``response[username]`` contains the user identifier for the
                server, and may contain extra user-attributes.

        Returns:
            `SocialLogin()` object: State of the login-session.

        """
        login = self.provider.sociallogin_from_response(request, response)
        return login

    def get_service_url(self, request):
        """The service url, used by the CAS client.

        According to the CAS spec, the service url is passed by the CAS client
        at several times. It must be the same for all interactions with the CAS
        server.

        It is used as redirection from the CAS server after a succssful
        authentication. So, the callback url is used as service url.

        If present, the GET param ``next`` is added to the service url.
        """
        redirect_to = get_next_redirect_url(request)

        callback_kwargs = {'next': redirect_to} if redirect_to else {}
        callback_url = (
            self.provider.get_callback_url(request, **callback_kwargs))

        service_url = request.build_absolute_uri(callback_url)

        return service_url


class CASView(object):
    """
    Base class for CAS views.
    """
    @classmethod
    def adapter_view(cls, adapter):
        """Transform the view class into a view function.

        Similar to the Django ``as_view()`` method.

        Notes:
            An (human) error page is rendered if any ``CASAuthenticationError``
            is catched.

        Args:
            adapter (:class:`CASAdapter`): Provide specifics of a CAS server.

        Returns:
            A view function. The given adapter and related provider are
            accessible as attributes from the view class.


        """
        def view(request, *args, **kwargs):
            # Prepare the func-view.
            self = cls()

            self.request = request
            self.args = args
            self.kwargs = kwargs

            # Setup and store adapter as view attribute.
            self.adapter = adapter(request)
            self.provider = self.adapter.provider

            try:
                return self.dispatch(request, *args, **kwargs)
            except CASAuthenticationError:
                return self.render_error()

        return view

    def get_client(self, request, action=AuthAction.AUTHENTICATE):
        """
        Returns the CAS client to interact with the CAS server.
        """
        auth_params = self.provider.get_auth_params(request, action)

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
        return render_authentication_error(self.request, self.provider.id)


class CASLoginView(CASView):

    def dispatch(self, request):
        """
        Redirects to the CAS server login page.
        """
        action = request.GET.get('action', AuthAction.AUTHENTICATE)
        SocialLogin.stash_state(request)
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

        uid, extra, _ = response

        if not uid:
            raise CASAuthenticationError(
                "CAS server doesn't validate the ticket."
            )

        # Keep tracks of the last used CAS provider.
        request.session[CAS_PROVIDER_SESSION_KEY] = self.provider.id

        data = (uid, extra or {})

        # Finish the login flow.
        login = self.adapter.complete_login(request, data)
        login.state = SocialLogin.unstash_state(request)
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
        Returns the url to redirect after logout.
        """
        request = self.request
        return (
            get_next_redirect_url(request) or
            get_adapter(request).get_logout_redirect_url(request)
        )
