# -*- coding: utf-8 -*-
import django

if django.VERSION >= (2, 0):
    from django.urls import include, re_path as url
else:
    from django.conf.urls import include, url

urlpatterns = [
    url(r'^example/', include('tests.example.urls')),
    url(r'^accounts/', include('allauth.urls')),
]
