"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from tests.norm.utils import NormTestCase


class NamespaceTestCase(NormTestCase):

    def test_importing(self):
        script = """
        import norm.test.*;
        """
        self.execute(script)
        self.assertTrue('norm.test' in self.executor.search_namespaces)

    def test_importing_type(self):
        self.execute("Tester(dummy:Integer);")
        self.execute("export Tester norm.test;")
        lam = self.execute("import norm.test.Tester;")
        self.assertTrue('norm.test' in self.executor.search_namespaces)
        # lam = retrieve_type(self.executor.context_namespace, 'Tester', None, self.session)
        self.assertTrue(lam is not None)

    def test_renaming(self):
        self.execute("Tester(dummy:Integer);")
        self.execute("export Tester norm.test;")
        lam = self.execute("import norm.test.Tester as tt;")
        self.assertTrue('norm.test' in self.executor.search_namespaces)
        self.assertTrue(lam is not None)
        self.assertTrue(lam.namespace == self.executor.context_namespace)
        self.assertTrue(lam.name == 'tt')

    def test_exporting(self):
        self.execute("Tester(dummy:Integer);")
        lam = self.execute("export Tester norm.test2 as Tester2;")
        self.assertTrue(lam is not None)
        self.assertTrue(lam.namespace == 'norm.test2')
        self.assertTrue(lam.name == 'Tester2')
