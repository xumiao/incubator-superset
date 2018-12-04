"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from tests.norm.utils import user_tester
from norm.config import db
from norm.engine import execute


class DeclarationTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()
        self.context_id = 'testing'

    def test_recognize_declaration(self):
        script = """
        Company(name: String, description: String, founders: [String], founded_at: Datetime);
        """
        lam = execute(script, self.session, self.context_id)
        self.assertTrue(lam is not None)

    def test_recognize_repeated_declaration_within_the_same_session(self):
        script = """
        Company(name: String, description: String, founders: [String], founded_at: Datetime);
        """
        company = execute(script, self.session, self.context_id)
        assert(company is not None)

        new_company = execute(script, self.session, self.context_id)
        assert(company.id == new_company.id)

