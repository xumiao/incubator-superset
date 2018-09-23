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
        cmd = exe.stack.pop()
        string_type = engine.TypeName('String', None)
        pt_type = engine.UnionType([engine.TypeName('Person', None), engine.TypeName('Teacher', None)])
        list_type = engine.ListType(pt_type)
        datetime_type = engine.TypeName('DateTime', None)
        self.assertEqual(cmd, engine.FullTypeDeclaration('', engine.TypeDefinition(engine.TypeName('Company', None),
                                                                                   engine.ArgumentDeclarations([
                                                                                       engine.ArgumentDeclaration(
                                                                                           'name', string_type
                                                                                       ),
                                                                                       engine.ArgumentDeclaration(
                                                                                           'description', string_type
                                                                                       ),
                                                                                       engine.ArgumentDeclaration(
                                                                                           'founders', list_type
                                                                                       ),
                                                                                       engine.ArgumentDeclaration(
                                                                                           'founded_at', datetime_type
                                                                                       )
                                                                                   ]), None),
                                                         engine.TypeImpl('query', '')))

