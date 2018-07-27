"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from textwrap import dedent
from norm import engine
import re
from dateutil import parser as dateparser


class ExpressionTestCase(unittest.TestCase):

    constant_tests = {
        "null;": ('none', None),
        "true;": ('bool', True),
        "false;": ('bool', False),
        "34;": ('int', 34),
        "34.343;": ('float', 34.343),
        "'test';": ('string', 'test'),
        "u'test';": ('unicode', b'test'),
        "r'test';": ('pattern', re.compile('test')),
        "$'sfs2123';": ('uuid', 'sfs2123'),
        "l'http://example.com';": ('url', 'http://example.com'),
        "t'2018/08/12 23:34:01';": ('datetime', dateparser.parse('2018/08/12 23:34:01', fuzzy=True))
    }

    base_expression_tests = {
        "true;": ('constant', engine.Constant('bool', True)),
        "Test;": ('type', engine.TypeName('Test', None)),
        "test;": ('variable', 'test')
    }

    def test_recognize_constant(self):
        for s, (t, v) in self.constant_tests.items():
            exe = engine.compile_norm(s)
            cmd = exe.stack.pop()
            self.assertEqual(cmd.type_name, t)
            self.assertEqual(cmd.value, v)

    def test_recognize_base_expression(self):
        for s, (t, v) in self.base_expression_tests.items():
            exe = engine.compile_norm(s)
            cmd = exe.stack.pop()
            self.assertEqual(cmd.type_name, t)
            self.assertEqual(cmd.value, v)

    def test_recognize_list_expression(self):
        script = dedent("""
        [2.3, 1.1];
        """)
        exe = engine.compile_norm(script)
        cmd = exe.stack.pop()
        self.assertEqual(cmd.elements, [2.3, 1.1])