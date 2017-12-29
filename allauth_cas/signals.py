# -*- coding: utf-8 -*-
from django.contrib.auth.signals import user_logged_out
from django.dispatch import receiver

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

    if not provider.message_suggest_caslogout_on_logout(request):
        return

    next_page = (
        get_next_redirect_url(request) or
        get_adapter(request).get_logout_redirect_url(request)
    )

    provider.add_message_suggest_caslogout(
        request, next_page=next_page,
        level=provider.message_suggest_caslogout_on_logout_level(request),
    )
