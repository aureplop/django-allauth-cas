# -*- coding: utf-8 -*-
from allauth_cas.urls import default_urlpatterns

from .provider import ExampleCASProvider

urlpatterns = default_urlpatterns(ExampleCASProvider)
