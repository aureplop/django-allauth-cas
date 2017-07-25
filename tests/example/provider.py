# -*- coding: utf-8 -*-
from allauth.socialaccount.providers.base import ProviderAccount

from allauth_cas.providers import CASProvider


class ExampleCASAccount(ProviderAccount):
    pass


class ExampleCASProvider(CASProvider):
    id = 'theid'
    name = 'The Provider'
    account_class = ExampleCASAccount


provider_classes = [ExampleCASProvider]
