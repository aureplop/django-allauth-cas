# -*- coding: utf-8 -*-
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver
from django.utils.safestring import mark_safe

from allauth.account.adapter import get_adapter
from allauth.account.utils import get_next_redirect_url
from allauth.socialaccount import providers

from . import CAS_PROVIDER_SESSION_KEY


@receiver(user_logged_out)
def cas_account_logout(sender, request, **kwargs):
    provider_id = request.session.get(CAS_PROVIDER_SESSION_KEY)

    if not provider_id:
        return

    provider = providers.registry.by_id(provider_id, request)

    if not provider.message_on_logout(request):
        return

    adapter = get_adapter(request)

    redirect_url = (
        get_next_redirect_url(request) or
        adapter.get_logout_redirect_url(request)
    )

    logout_kwargs = {'next': redirect_url} if redirect_url else {}
    logout_url = provider.get_logout_url(request, **logout_kwargs)

    level = provider.message_on_logout_level(request)
    logout_link = mark_safe('<a href="{}">link</a>'.format(logout_url))

    adapter.add_message(
        request, level,
        message_template='cas_account/messages/logged_out.txt',
        message_context={
            'logout_url': logout_url,
            'logout_link': logout_link,
        }
    )
