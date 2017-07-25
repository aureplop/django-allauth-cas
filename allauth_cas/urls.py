# -*- coding: utf-8 -*-
from django.conf.urls import include, url

from allauth.utils import import_attribute


def default_urlpatterns(provider):
    package = provider.get_package()

    login_view = import_attribute(package + '.views.login')
    callback_view = import_attribute(package + '.views.callback')
    logout_view = import_attribute(package + '.views.logout')

    urlpatterns = [
        url('^login/$',
            login_view, name=provider.id + '_login'),
        url('^login/callback/$',
            callback_view, name=provider.id + '_callback'),
        url('^logout/$',
            logout_view, name=provider.id + '_logout'),
    ]

    return [url('^' + provider.get_slug() + '/', include(urlpatterns))]
