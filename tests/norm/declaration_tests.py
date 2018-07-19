"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from textwrap import dedent
from norm import engine


class DeclarationTestCase(unittest.TestCase):

    def test_recognize_declaration(self):
        script = dedent("""
        Company(name: String, description: String, founders: List[Person|Teacher], founded_at: DateTime) = {};
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.imports, ['norm.test'])

