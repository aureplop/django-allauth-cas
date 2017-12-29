# -*- coding: utf-8 -*-
import os

from setuptools import find_packages, setup

from allauth_cas import __version__

BASE_DIR = os.path.dirname(__file__)

with open(os.path.join(BASE_DIR, 'README.rst')) as readme:
    README = readme.read()

setup(
    name='django-allauth-cas',
    version=__version__,
    description='CAS support for django-allauth.',
    author='Aurélien Delobelle',
    author_email='aurelien.delobelle@gmail.com',
    keywords='django allauth cas authentication',
    long_description=README,
    url='https://github.com/aureplop/django-allauth-cas',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
    ],
    license='MIT',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    install_requires=[
        'django-allauth',
        'python-cas',
        'six',
    ],
    extras_require={
        'docs': ['sphinx'],
        'tests': ['tox'],
    },
)
