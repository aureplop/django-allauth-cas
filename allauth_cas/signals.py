# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount import providers

from . import CAS_PROVIDER_SESSION_KEY


@receiver(user_logged_out)
def cas_account_logout(sender, request, **kwargs):
    provider_id = request.session.get(CAS_PROVIDER_SESSION_KEY)

    if (not provider_id or
            'django.contrib.messages' not in settings.INSTALLED_APPS):
        return

    provider = providers.registry.by_id(provider_id, request)

    if not provider.message_on_logout(request):
        return

    redirect_url = (
        get_next_redirect_url(request) or
        request.get_full_path()
    )

    logout_kwargs = {'next': redirect_url} if redirect_url else {}
    logout_url = provider.get_logout_url(request, **logout_kwargs)
    logout_link = mark_safe('<a href="{}">link</a>'.format(logout_url))

    level = provider.message_on_logout_level(request)

    # DefaultAccountAdapter.add_message from allauth.account.adapter is
    # unusable because HTML in message content is always escaped.

    template = 'cas_account/messages/logged_out.txt'
    context = {
        'logout_url': logout_url,
        'logout_link': logout_link,
    }

    message = mark_safe(render_to_string(template, context).strip())

    messages.add_message(request, level, message)
