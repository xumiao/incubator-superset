"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
import uuid

from tests.norm.utils import user_tester
from norm.config import db
from norm.engine import execute, get_context, retrieve_type


class NamespaceTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = user_tester()
        self.context_id = str(uuid.uuid4())
        execute("Tester(dummy:Integer);", self.session, self.context_id)
        execute("export Tester norm.test;", self.session, self.context_id)
        self.context_id = str(uuid.uuid4())

    def tearDown(self):
        self.session.rollback()
        self.session.close()

    def test_importing(self):
        script = """
        import norm.test.*;
        """
        execute(script, self.session, self.context_id)
        context = get_context(self.context_id)
        self.assertTrue('norm.test' in context.search_namespaces)

    def test_importing_type(self):
        script = """
        import norm.test.Tester;
        """
        execute(script, self.session, self.context_id)
        context = get_context(self.context_id)
        self.assertTrue('norm.test' in context.search_namespaces)
        lam = retrieve_type(context.context_namespace, 'Tester', 1, self.session)
        self.assertTrue(lam is not None)

    def test_renaming(self):
        script = """
        import norm.test.Tester as tt;
        """
        execute(script, self.session, self.context_id)
        context = get_context(self.context_id)
        self.assertTrue('norm.test' in context.search_namespaces)
        lam = retrieve_type(context.context_namespace, 'tt', 1, self.session)
        self.assertTrue(lam is not None)

    def test_exporting(self):
        context_id = str(uuid.uuid4())
        execute("Tester(dummy:Integer);", self.session, context_id)
        execute("export Tester norm.test2 as Tester2;", self.session, context_id)
        lam = retrieve_type('norm.test2', 'Tester2', 1, self.session)
        self.assertTrue(lam is not None)
