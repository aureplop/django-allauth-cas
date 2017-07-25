# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class CASAccountConfig(AppConfig):
    name = 'allauth_cas'
    verbose_name = _("CAS Accounts")

    def ready(self):
        from . import signals  # noqa
