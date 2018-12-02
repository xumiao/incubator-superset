"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from tests.norm.utils import user_tester
from norm.config import db
from norm.engine import execute, get_context
from norm.models.norm import retrieve_type, Status


class DeclarationTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()

    def test_recognize_declaration(self):
        script = """
        Company(name: String, description: String, founders: [String], founded_at: Datetime);
        """
        lam = retrieve_type(None, 'Company', None, self.session, status=Status.DRAFT)
        if lam:
            previous_version = lam.version
        else:
            previous_version = 0
        execute(script, self.session)
        self.session.commit()
        lam = retrieve_type(None, 'Company', None, self.session, status=Status.DRAFT)
        assert(lam is not None)
        assert(lam.version > previous_version)

    def test_recognize_repeated_declaration_within_the_same_session(self):
        script = """
        Company(name: String, description: String, founders: [String], founded_at: Datetime);
        """
        context_id = 0
        company = execute(script, self.session, context_id)
        assert(company is not None)

        new_company = execute(script, self.session, context_id)
        assert(company.id == new_company.id)

