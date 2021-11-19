from __future__ import division, absolute_import, print_function

import confuse
import os
import unittest
from . import _root


ENVIRON = os.environ


class EnvSourceTest(unittest.TestCase):
    def setUp(self):
        os.environ = {}

    def tearDown(self):
        os.environ = ENVIRON

    def test_prefix(self):
        os.environ['TEST_FOO'] = 'a'
        os.environ['BAR'] = 'b'
        config = _root(confuse.EnvSource('TEST_'))
        self.assertEqual(config.get(), {'foo': 'a'})

    def test_number_type_conversion(self):
        os.environ['TEST_FOO'] = '1'
        os.environ['TEST_BAR'] = '2.0'
        config = _root(confuse.EnvSource('TEST_'))
        foo = config['foo'].get()
        bar = config['bar'].get()
        self.assertIsInstance(foo, int)
        self.assertEqual(foo, 1)
        self.assertIsInstance(bar, float)
        self.assertEqual(bar, 2.0)

    def test_bool_type_conversion(self):
        os.environ['TEST_FOO'] = 'true'
        os.environ['TEST_BAR'] = 'FALSE'
        config = _root(confuse.EnvSource('TEST_'))
        self.assertIs(config['foo'].get(), True)
        self.assertIs(config['bar'].get(), False)

    def test_null_type_conversion(self):
        os.environ['TEST_FOO'] = 'null'
        os.environ['TEST_BAR'] = ''
        config = _root(confuse.EnvSource('TEST_'))
        self.assertIs(config['foo'].get(), None)
        self.assertIs(config['bar'].get(), None)

    def test_unset_lower_config(self):
        os.environ['TEST_FOO'] = 'null'
        config = _root({'foo': 'bar'})
        self.assertEqual(config['foo'].get(), 'bar')
        config.set(confuse.EnvSource('TEST_'))
        self.assertIs(config['foo'].get(), None)

    def test_sep_default(self):
        os.environ['TEST_FOO__BAR'] = 'a'
        os.environ['TEST_FOO_BAZ'] = 'b'
        config = _root(confuse.EnvSource('TEST_'))
        self.assertEqual(config['foo']['bar'].get(), 'a')
        self.assertEqual(config['foo_baz'].get(), 'b')

    def test_sep_single_underscore_adjacent_seperators(self):
        os.environ['TEST_FOO__BAR'] = 'a'
        os.environ['TEST_FOO_BAZ'] = 'b'
        config = _root(confuse.EnvSource('TEST_', sep='_'))
        self.assertEqual(config['foo']['']['bar'].get(), 'a')
        self.assertEqual(config['foo']['baz'].get(), 'b')

    def test_nested(self):
        os.environ['TEST_FOO__BAR'] = 'a'
        os.environ['TEST_FOO__BAZ__QUX'] = 'b'
        config = _root(confuse.EnvSource('TEST_'))
        self.assertEqual(config['foo']['bar'].get(), 'a')
        self.assertEqual(config['foo']['baz']['qux'].get(), 'b')

    def test_nested_rev(self):
        # Reverse to ensure order doesn't matter
        os.environ['TEST_FOO__BAZ__QUX'] = 'b'
        os.environ['TEST_FOO__BAR'] = 'a'
        config = _root(confuse.EnvSource('TEST_'))
        self.assertEqual(config['foo']['bar'].get(), 'a')
        self.assertEqual(config['foo']['baz']['qux'].get(), 'b')

    def test_nested_clobber(self):
        os.environ['TEST_FOO__BAR'] = 'a'
        os.environ['TEST_FOO__BAR__BAZ'] = 'b'
        config = _root(confuse.EnvSource('TEST_'))
        # Clobbered
        self.assertEqual(config['foo']['bar'].get(), {'baz': 'b'})
        self.assertEqual(config['foo']['bar']['baz'].get(), 'b')

    def test_nested_clobber_rev(self):
        # Reverse to ensure order doesn't matter
        os.environ['TEST_FOO__BAR__BAZ'] = 'b'
        os.environ['TEST_FOO__BAR'] = 'a'
        config = _root(confuse.EnvSource('TEST_'))
        # Clobbered
        self.assertEqual(config['foo']['bar'].get(), {'baz': 'b'})
        self.assertEqual(config['foo']['bar']['baz'].get(), 'b')

    def test_lower_applied_after_prefix_match(self):
        os.environ['TEST_FOO'] = 'a'
        config = _root(confuse.EnvSource('test_', lower=True))
        self.assertEqual(config.get(), {})

    def test_lower_already_lowercase(self):
        os.environ['TEST_foo'] = 'a'
        config = _root(confuse.EnvSource('TEST_', lower=True))
        self.assertEqual(config.get(), {'foo': 'a'})

    def test_lower_does_not_alter_value(self):
        os.environ['TEST_FOO'] = 'UPPER'
        config = _root(confuse.EnvSource('TEST_', lower=True))
        self.assertEqual(config.get(), {'foo': 'UPPER'})

    def test_lower_false(self):
        os.environ['TEST_FOO'] = 'a'
        config = _root(confuse.EnvSource('TEST_', lower=False))
        self.assertEqual(config.get(), {'FOO': 'a'})

    def test_handle_lists_good_list(self):
        os.environ['TEST_FOO__0'] = 'a'
        os.environ['TEST_FOO__1'] = 'b'
        os.environ['TEST_FOO__2'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), ['a', 'b', 'c'])

    def test_handle_lists_good_list_rev(self):
        # Reverse to ensure order doesn't matter
        os.environ['TEST_FOO__2'] = 'c'
        os.environ['TEST_FOO__1'] = 'b'
        os.environ['TEST_FOO__0'] = 'a'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), ['a', 'b', 'c'])

    def test_handle_lists_nested_lists(self):
        os.environ['TEST_FOO__0__0'] = 'a'
        os.environ['TEST_FOO__0__1'] = 'b'
        os.environ['TEST_FOO__1__0'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), [['a', 'b'], ['c']])

    def test_handle_lists_bad_list_missing_index(self):
        os.environ['TEST_FOO__0'] = 'a'
        os.environ['TEST_FOO__2'] = 'b'
        os.environ['TEST_FOO__3'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), {'0': 'a', '2': 'b', '3': 'c'})

    def test_handle_lists_bad_list_non_zero_start(self):
        os.environ['TEST_FOO__1'] = 'a'
        os.environ['TEST_FOO__2'] = 'b'
        os.environ['TEST_FOO__3'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), {'1': 'a', '2': 'b', '3': 'c'})

    def test_handle_lists_bad_list_non_numeric(self):
        os.environ['TEST_FOO__0'] = 'a'
        os.environ['TEST_FOO__ONE'] = 'b'
        os.environ['TEST_FOO__2'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), {'0': 'a', 'one': 'b', '2': 'c'})

    def test_handle_lists_top_level_always_dict(self):
        os.environ['TEST_0'] = 'a'
        os.environ['TEST_1'] = 'b'
        os.environ['TEST_2'] = 'c'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config.get(), {'0': 'a', '1': 'b', '2': 'c'})

    def test_handle_lists_not_a_list(self):
        os.environ['TEST_FOO__BAR'] = 'a'
        os.environ['TEST_FOO__BAZ'] = 'b'
        config = _root(confuse.EnvSource('TEST_', handle_lists=True))
        self.assertEqual(config['foo'].get(), {'bar': 'a', 'baz': 'b'})
