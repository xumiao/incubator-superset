"""Unit tests for Norm"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import unittest
from norm import execute
from superset import db


class CommentsTestCase(unittest.TestCase):

    def setUp(self):
        self.session = db.session
        self.user = 'tester'

    def test_recognize_single_line_comment1(self):
        script = """
        // Comment 1
        ;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, 'Comment 1')

    def test_recognize_single_line_comment2(self):
        script = """
        // \tComment 2
        ;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, 'Comment 2')

    def test_fail_single_line_comment1(self):
        script = """
        // 
        Comment 3
        ;
        """
        with self.assertRaises(ValueError):
            execute(script, self.session, self.user)

    def test_recognize_multi_line_comment1(self):
        script = """
        /* Comment 4 */
        ;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, 'Comment 4')

    def test_recognize_multi_line_comment2(self):
        script = """
        /*
            Comment 5 
        */
        ;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, "Comment 5")

    def test_recognize_multi_line_comment3(self):
        script = """
        /*
            Comment 6
            and
            more ...
        */
        ;
        """
        exe = execute(script, self.session, self.user)
        self.assertEqual(exe, "Comment 6\n    and\n    more ...")

    def test_fail_multi_line_comment4(self):
        script = """
        /*
            Comment 7
            no end
        """
        with self.assertRaises(ValueError):
            execute(script, self.session, self.user)

