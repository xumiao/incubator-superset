"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from textwrap import dedent
from norm import engine


class CommentsTestCase(unittest.TestCase):

    def test_recognize_single_line_comment1(self):
        script = dedent("""
        // Comment 1
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.comments, ' Comment 1')

    def test_recognize_single_line_comment2(self):
        script = dedent("""
        // \tComment 2
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.comments, ' \tComment 2')

    def test_fail_single_line_comment1(self):
        script = dedent("""
        // 
        Comment 3
        """)
        with self.assertRaises(ValueError):
            engine.compile_norm(script)

    def test_recognize_multi_line_comment1(self):
        script = dedent("""
        /* Comment 4 */
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.comments, ' Comment 4 ')

    def test_recognize_multi_line_comment2(self):
        script = dedent("""
        /*
            Comment 5 
        */
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.comments, "\n    Comment 5 \n")

    def test_recognize_multi_line_comment3(self):
        script = dedent("""
        /*
            Comment 6
            and
            more ...
        */
        """)
        exe = engine.compile_norm(script)
        self.assertEqual(exe.comments, "\n    Comment 6\n    and\n    more ...\n")

    def test_fail_multi_line_comment4(self):
        script = dedent("""
        /*
            Comment 7
            no end
        """)
        with self.assertRaises(ValueError):
            engine.compile_norm(script)

