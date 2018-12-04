"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest

from tests.norm.utils import user_tester
from norm.config import db
from norm.engine import execute


class VersioningTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()
        self.context_id = 'testing'

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_same_version_for_draft(self):
        lam = execute("version_test(test:Integer);", self.session, self.context_id)
        script = """
        // revising a draft has the same version
        version_test(test:Integer, test2:String);
        """
        lam2 = execute(script, self.session, self.context_id)
        self.assertTrue(lam2.version == lam.version)

    def test_version_up(self):
        execute("version_test(test:Integer);", self.session, self.context_id)
        lam1 = execute("export version_test;", self.session, self.context_id)
        execute("version_test(test:Integer, test2:String);", self.session, self.context_id)
        lam2 = execute("export version_test;", self.session, self.context_id)
        self.assertTrue(lam2.version > lam1.version)
        self.assertTrue(lam2.cloned_from is lam1)

