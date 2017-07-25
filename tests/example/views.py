# -*- coding: utf-8 -*-
from allauth_cas import views

from .provider import ExampleCASProvider


class ExampleCASAdapter(views.CASAdapter):
    provider_id = ExampleCASProvider.id
    url = 'https://server.cas'
    version = 2


login = views.CASLoginView.adapter_view(ExampleCASAdapter)
callback = views.CASCallbackView.adapter_view(ExampleCASAdapter)
logout = views.CASLogoutView.adapter_view(ExampleCASAdapter)
