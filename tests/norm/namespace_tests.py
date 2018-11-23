"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from tests.norm.utils import user_tester
from norm.config import db
from norm.engine import execute, get_compiler


class NamespaceTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()

    def test_recognize_importing(self):
        script = """
        using norm.test;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, 'norm.test')

    def test_recognize_importing_type(self):
        script = """
        using norm.test.tester@3;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, 'norm.test')

    def test_recognize_renaming(self):
        script = """
        using norm.test.tester@4 as tt;
        """
        exe = execute(script, self.session, self.user, 0)
        self.assertEqual(exe, 'norm.test')
        c = get_compiler(0)
        self.assertTrue('tt' in c.variables)
