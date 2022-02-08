# -*- coding: utf-8 -*-
import django
from django.apps import AppConfig

if django.VERSION >= (2, 0):
    from django.utils.translation import gettext_lazy as _
else:
    from django.utils.translation import ugettext_lazy as _


class CASAccountConfig(AppConfig):
    name = 'allauth_cas'
    verbose_name = _("CAS Accounts")

    def ready(self):
        from . import signals  # noqa
