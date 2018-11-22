"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from tests.norm.utils import user_tester
from norm import execute
from superset import db


class DeclarationTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()

    def test_recognize_declaration(self):
        script = """
        Company(name: String, description: String, founders: [String], founded_at: Datetime);
        """
        res = execute(script, self.session, self.user)

