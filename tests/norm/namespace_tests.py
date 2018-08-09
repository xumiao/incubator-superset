"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from textwrap import dedent
from norm import engine


class NamespaceTestCase(unittest.TestCase):

    def test_recognize_importing(self):
        script = dedent("""
        import norm.test;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.imports, ['norm.test'])

    def test_recognize_namespace(self):
        script = dedent("""
        namespace norm.test;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.namespace, 'norm.test')

    def test_recognize_multiple_imports(self):
        script = dedent("""
        import norm.test;
        import norm.base;
        import norm.nn;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.imports, ['norm.test', 'norm.base', 'norm.nn'])

    def test_recognize_switch_namespace(self):
        script = dedent("""
        namespace norm.test;
        namespace norm.nn;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.namespace, 'norm.nn')

    def test_recognize_mixed_namespace_imports(self):
        script = dedent("""
        namespace norm.test;
        import norm.nn;
        namespace norm.base;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.namespace, 'norm.base')
        self.assertEqual(exe.imports, ['norm.nn'])

    def test_imports_type(self):
        script = dedent("""
        import norm.natives.Any;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.imports, ['norm.natives'])
        self.assertEqual(exe.alias, {'Any': engine.TypeName('Any', None)})

    def test_imports_type_alias(self):
        script = dedent("""
        import norm.natives.Any@3 as All;
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.imports, ['norm.natives'])
        self.assertEqual(exe.alias, {'All': engine.TypeName('Any', 3)})
