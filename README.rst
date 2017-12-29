##################
django-allauth-cas
##################

.. image:: https://travis-ci.org/aureplop/django-allauth-cas.svg?branch=master
  :target: https://travis-ci.org/aureplop/django-allauth-cas

.. image:: https://coveralls.io/repos/github/aureplop/django-allauth-cas/badge.svg?branch=master
  :target: https://coveralls.io/github/aureplop/django-allauth-cas?branch=master


CAS support for django-allauth_.

Requirements
  * Django 1.8 → 2.0

Dependencies
  * django-allauth_
  * python-cas_: CAS client library

.. note::

  Tests only target the latest allauth version compatible for each Django version
  supported:

  * Django 1.9 with django-allauth 0.32.0;
  * Django 1.8, 1.10, 1.11, 2.0 with the latest django-allauth.

If you have any problems at use or think docs can be clearer, take a little
time to open an issue and/or a PR would be welcomed ;-)

Acknowledgments
  * This work is strongly inspired by the `OAuth2 support of django-allauth`_.


************
Installation
************

Install the python package ``django-allauth-cas``. For example, using pip:

.. code-block:: bash

  $ pip install django-allauth-cas

Add ``'allauth_cas'`` to ``INSTALLED_APPS``.


.. _django-allauth: https://github.com/pennersr/django-allauth
.. _OAuth2 support of django-allauth: https://github.com/pennersr/django-allauth/tree/master/allauth/socialaccount/providers/oauth2
.. _python-cas: https://github.com/python-cas/python-cas
