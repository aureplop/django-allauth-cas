# -*- coding: utf-8 -*-
import cas


class MockCASClient(cas.CASClientV2):
    """
    Base class to mock cas.CASClient
    """
    def __init__(self, *args, **kwargs):
        kwargs.pop('version')
        super(MockCASClient, self).__init__(*args, **kwargs)


class VerifyCASClient(MockCASClient):
    """
    CAS client which verifies ticket is '123456'.
    """
    def verify_ticket(self, ticket):
        if ticket == '123456':
            return 'username', {}, None
        return None, {}, None


class AcceptCASClient(MockCASClient):
    """
    CAS client which accepts all tickets.
    """
    def verify_ticket(self, ticket):
        return 'username', {}, None


class RejectCASClient(MockCASClient):
    """
    CAS client which rejects all tickets.
    """
    def verify_ticket(self, ticket):
        return None, {}, None
