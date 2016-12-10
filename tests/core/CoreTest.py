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
        # General test which makes use of the full dependency chain from the
        # defined above.
        bear_e = BearE_NeedsAD(Section('test-section'))
        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_e})

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

        # Finally check the bears_to_schedule
        self.assertEqual(bears_to_schedule, {bear_a, bear_b})

    def test_initialize_dependencies2(self):
        # Test simple case without dependencies.
        section = Section('test-section')
        bear_a = BearA(section)
        bear_b = BearB(section)
        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_a, bear_b})

        self.assertTrue(dependency_tracker.all_dependencies_resolved)

        self.assertEqual(bears_to_schedule, {bear_a, bear_b})

    def test_initialize_dependencies3(self):
        # Test whether pre-instantiated dependency bears are correctly
        # (re)used.
        section = Section('test-section')
        bear_b = BearB(section)
        bear_c = BearC_NeedsB(section)
        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_b, bear_c})

        self.assertEqual(dependency_tracker.get_all_dependants(), {bear_c})
        self.assertEqual(dependency_tracker.get_dependencies(bear_c), {bear_b})

        self.assertEqual(bears_to_schedule, {bear_b})

    def test_initialize_dependencies4(self):
        # Test whether pre-instantiated bears which belong to different
        # sections are not (re)used, as the sections are different.
        section1 = Section('test-section1')
        section2 = Section('test-section2')

        bear_b = BearB(section1)
        bear_c = BearC_NeedsB(section2)
        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_b, bear_c})

        self.assertEqual(dependency_tracker.get_all_dependants(), {bear_c})
        dependencies = dependency_tracker.get_all_dependencies()
        self.assertEqual(len(dependencies), 1)
        dependency = dependencies.pop()
        self.assertIsInstance(dependency, BearB)
        self.assertIsNot(dependency, bear_b)

        self.assertEqual(bears_to_schedule, {bear_b, dependency})

    def test_initialize_dependencies5(self):
        # Test whether two bears of same type but different sections get their
        # own dependency bear instances.
        section1 = Section('test-section1')
        section2 = Section('test-section2')

        bear_c_section1 = BearC_NeedsB(section1)
        bear_c_section2 = BearC_NeedsB(section2)

        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_c_section1, bear_c_section2})

        # Test path for section1
        bear_c_s1_dependencies = dependency_tracker.get_dependencies(
            bear_c_section1)
        self.assertEqual(len(bear_c_s1_dependencies), 1)
        bear_b_section1 = bear_c_s1_dependencies.pop()
        self.assertIsInstance(bear_b_section1, BearB)

        # Test path for section2
        bear_c_s2_dependencies = dependency_tracker.get_dependencies(
            bear_c_section2)
        self.assertEqual(len(bear_c_s2_dependencies), 1)
        bear_b_section2 = bear_c_s2_dependencies.pop()
        self.assertIsInstance(bear_b_section2, BearB)

        # Test if both dependencies aren't the same.
        self.assertIsNot(bear_b_section1, bear_b_section2)

        # Test bears for schedule.
        self.assertEqual(bears_to_schedule, {bear_b_section1, bear_b_section2})

    def test_initialize_dependencies6(self):
        # Test whether two pre-instantiated dependencies with the same section
        # are correctly registered as dependencies, so only a single one of
        # those instances should be picked as a dependency.
        section = Section('test-section')

        bear_c = BearC_NeedsB(section)
        bear_b1 = BearB(section)
        bear_b2 = BearB(section)

        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_c, bear_b1, bear_b2})

        bear_c_dependencies = dependency_tracker.get_dependencies(bear_c)
        self.assertEqual(len(bear_c_dependencies), 1)
        bear_c_dependency = bear_c_dependencies.pop()
        self.assertIsInstance(bear_c_dependency, BearB)

        self.assertIn(bear_c_dependency, {bear_b1, bear_b2})

        self.assertEqual(bears_to_schedule, {bear_b1, bear_b2})

    def test_initialize_dependencies7(self):
        # Test if a single dependency instance is created for two different
        # instances pointing to the same section.
        section = Section('test-section')

        bear_c1 = BearC_NeedsB(section)
        bear_c2 = BearC_NeedsB(section)

        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_c1, bear_c2})

        # Test first path.
        bear_c1_dependencies = dependency_tracker.get_dependencies(bear_c1)
        self.assertEqual(len(bear_c1_dependencies), 1)
        bear_b1 = bear_c1_dependencies.pop()
        self.assertIsInstance(bear_b1, BearB)

        # Test second path.
        bear_c2_dependencies = dependency_tracker.get_dependencies(bear_c2)
        self.assertEqual(len(bear_c2_dependencies), 1)
        bear_b2 = bear_c2_dependencies.pop()
        self.assertIsInstance(bear_b2, BearB)

        # Test if both dependencies are actually the same.
        self.assertIs(bear_b1, bear_b2)

    def test_initialize_dependencies8(self):
        # Test totally empty case.
        dependency_tracker, bears_to_schedule = initialize_dependencies(set())

        self.assertTrue(dependency_tracker.all_dependencies_resolved)
        self.assertEqual(bears_to_schedule, set())
