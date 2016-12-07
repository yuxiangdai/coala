import unittest

from coalib.settings.Section import Section
from coalib.core.Bear import Bear
from coalib.core.Core import initialize_dependencies


class BearA(Bear):
    DEPENDENCIES = set()


class BearB(Bear):
    DEPENDENCIES = set()


class BearC_NeedsB(Bear):
    DEPENDENCIES = {BearB}


class BearD_NeedsC(Bear):
    DEPENDENCIES = {BearC_NeedsB}


class BearE_NeedsAD(Bear):
    DEPENDENCIES = {BearA, BearD_NeedsC}


class CoreTest(unittest.TestCase):
    def test_initialize_dependencies1(self):
        bear_e = BearE_NeedsAD(Section('test-section'))
        dependency_tracker = initialize_dependencies({bear_e})

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_e)), 2)
        self.assertTrue(any(isinstance(bear, BearA) for bear in
                            dependency_tracker.get_dependencies(bear_e)))
        self.assertTrue(any(isinstance(bear, BearD_NeedsC) for bear in
                            dependency_tracker.get_dependencies(bear_e)))

        bear_a = next(
            bear for bear in dependency_tracker.get_dependencies(bear_e)
            if isinstance(bear, BearA))
        bear_d = next(
            bear for bear in dependency_tracker.get_dependencies(bear_e)
            if isinstance(bear, BearD_NeedsC))

        self.assertIs(bear_a.section, bear_e.section)
        self.assertIs(bear_d.section, bear_e.section)

        self.assertEqual(dependency_tracker.get_dependencies(bear_a), set())

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_d)), 1)
        bear_c = dependency_tracker.get_dependencies(bear_d).pop()
        self.assertIs(bear_c.section, bear_e.section)
        self.assertIsInstance(bear_c, BearC_NeedsB)

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_c)), 1)
        bear_b = dependency_tracker.get_dependencies(bear_c).pop()
        self.assertIs(bear_b.section, bear_e.section)
        self.assertIsInstance(bear_b, BearB)

        self.assertEqual(dependency_tracker.get_dependencies(bear_b), set())

    def test_initialize_dependencies2(self):
        section = Section('test-section')
        dependency_tracker = initialize_dependencies(
            {BearA(section), BearB(section)})

        self.assertTrue(dependency_tracker.all_dependencies_resolved)

    def test_initialize_dependencies3(self):
        # Test whether pre-instantiated dependency bears are correctly
        # (re)used.
        section = Section('test-section')
        bear_b = BearB(section)
        bear_c = BearC_NeedsB(section)
        dependency_tracker = initialize_dependencies({bear_b, bear_c})

        self.assertEqual(dependency_tracker.get_all_dependants(), {bear_c})
        self.assertEqual(dependency_tracker.get_dependencies(bear_c), {bear_b})

    def test_initialize_dependencies4(self):
        # Test whether pre-instantiated bears which belong to different
        # sections are not (re)used, as the sections are different.
        section1 = Section('test-section1')
        section2 = Section('test-section2')

        bear_b = BearB(section1)
        bear_c = BearC_NeedsB(section2)
        dependency_tracker = initialize_dependencies({bear_b, bear_c})

        self.assertEqual(dependency_tracker.get_all_dependants(), {bear_c})
        dependencies = dependency_tracker.get_all_dependencies()
        self.assertEqual(len(dependencies), 1)
        dependency = dependencies.pop()
        self.assertIsInstance(dependency, BearB)
        self.assertIsNot(dependency, bear_b)

        # TODO Test if we preinstantiate some bears, all bears, some bears
        # TODO   twice
        # TODO And the case when no dependencies at all occur! Test
        # TODO   multi-section setup, with and without dependencies.
