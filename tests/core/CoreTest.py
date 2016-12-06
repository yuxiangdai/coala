import unittest

from coalib.settings.Section import Section
from coalib.core.Bear import Bear
from coalib.core.Core import initialize_dependencies


class BearA(Bear):
    DEPENDENCIES = set()


class BearB(Bear):
    DEPENDENCIES = set()


class BearC(Bear):
    DEPENDENCIES = {BearB}


class BearD(Bear):
    DEPENDENCIES = {BearC}


class BearE(Bear):
    DEPENDENCIES = {BearA, BearD}


class CoreTest(unittest.TestCase):
    def test_initialize_dependencies(self):
        bear_e = BearE(Section('test-section'))
        dependency_tracker = initialize_dependencies({bear_e})

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_e)), 2)
        self.assertTrue(any(isinstance(bear, BearA) for bear in
                            dependency_tracker.get_dependencies(bear_e)))
        self.assertTrue(any(isinstance(bear, BearD) for bear in
                            dependency_tracker.get_dependencies(bear_e)))

        bear_a = next(
            bear for bear in dependency_tracker.get_dependencies(bear_e)
            if isinstance(bear, BearA))
        bear_d = next(
            bear for bear in dependency_tracker.get_dependencies(bear_e)
            if isinstance(bear, BearD))

        self.assertIs(bear_a.section, bear_e.section)
        self.assertIs(bear_d.section, bear_e.section)

        self.assertEqual(dependency_tracker.get_dependencies(bear_a), set())

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_d)), 1)
        bear_c = dependency_tracker.get_dependencies(bear_d).pop()
        self.assertIs(bear_c.section, bear_e.section)
        self.assertIsInstance(bear_c, BearC)

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_c)), 1)
        bear_b = dependency_tracker.get_dependencies(bear_c).pop()
        self.assertIs(bear_b.section, bear_e.section)
        self.assertIsInstance(bear_b, BearB)

        self.assertEqual(dependency_tracker.get_dependencies(bear_b), set())

        # TODO Test if we preinstantiate some bears, all bears, some bears twice
        # TODO And the case when no dependencies at all occur! Test multi-section
        # TODO   setup, with and without dependencies.
