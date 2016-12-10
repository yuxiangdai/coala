import unittest

from coalib.settings.Section import Section
from coalib.core.Bear import Bear
from coalib.core.Core import initialize_dependencies, run


class TestBear(Bear):
    DEPENDENCIES = set()

    def analyze(self, section_name, file_dict):
        # The bear can in fact return everything (so it's not bound to actual
        # `Result`s), but it must be at least an iterable.
        return [(section_name, file_dict)]

    def generate_tasks(self):
        # Choose single task parallelization for simplicity. Also use the
        # section name as a parameter instead of the section itself, as compare
        # operations on tests do not succeed on them due to the pickling of
        # multiprocessing to transfer objects to the other process, which
        # instantiates a new section on each transfer.
        return ((self.section.name, self.file_dict), {}),


class BearA(TestBear):
    pass


class BearB(TestBear):
    pass


class BearC_NeedsB(TestBear):
    DEPENDENCIES = {BearB}


class BearD_NeedsC(TestBear):
    DEPENDENCIES = {BearC_NeedsB}


class BearE_NeedsAD(TestBear):
    DEPENDENCIES = {BearA, BearD_NeedsC}


class CoreTest(unittest.TestCase):
    def test_initialize_dependencies1(self):
        # General test which makes use of the full dependency chain from the
        # defined above.
        bear_e = BearE_NeedsAD(Section('test-section'), {})
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
        filedict = {}

        bear_a = BearA(section, filedict)
        bear_b = BearB(section, filedict)
        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_a, bear_b})

        self.assertTrue(dependency_tracker.all_dependencies_resolved)

        self.assertEqual(bears_to_schedule, {bear_a, bear_b})

    def test_initialize_dependencies3(self):
        # Test whether pre-instantiated dependency bears are correctly
        # (re)used.
        section = Section('test-section')
        filedict = {}

        bear_b = BearB(section, filedict)
        bear_c = BearC_NeedsB(section, filedict)

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
        filedict = {}

        bear_b = BearB(section1, filedict)
        bear_c = BearC_NeedsB(section2, filedict)

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
        filedict = {}

        bear_c_section1 = BearC_NeedsB(section1, filedict)
        bear_c_section2 = BearC_NeedsB(section2, filedict)

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
        # and file-dictionary are correctly registered as dependencies, so only
        # a single one of those instances should be picked as a dependency.
        section = Section('test-section')
        filedict = {}

        bear_c = BearC_NeedsB(section, filedict)
        bear_b1 = BearB(section, filedict)
        bear_b2 = BearB(section, filedict)

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
        # instances pointing to the same section and file-dictionary.
        section = Section('test-section')
        filedict = {}

        bear_c1 = BearC_NeedsB(section, filedict)
        bear_c2 = BearC_NeedsB(section, filedict)

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

    def test_initialize_dependencies9(self):
        # Test whether pre-instantiated bears which have different
        # file-dictionaries assigned are not (re)used, as they have different
        # file-dictionaries.
        section = Section('test-section')
        filedict1 = {'f2': []}
        filedict2 = {'f1': []}

        bear_b = BearB(section, filedict1)
        bear_c = BearC_NeedsB(section, filedict2)

        dependency_tracker, bears_to_schedule = initialize_dependencies(
            {bear_b, bear_c})

        self.assertEqual(dependency_tracker.get_all_dependants(), {bear_c})
        dependencies = dependency_tracker.get_all_dependencies()
        self.assertEqual(len(dependencies), 1)
        dependency = dependencies.pop()
        self.assertIsInstance(dependency, BearB)
        self.assertIsNot(dependency, bear_b)

        self.assertEqual(bears_to_schedule, {bear_b, dependency})

    def test_run1(self):
        # Test single bear without dependencies case.
        section = Section('test-section')
        filedict = {}
        bear_a = BearA(section, filedict)

        results = []

        def on_result(result):
            results.append(result)

        run({bear_a}, on_result)

        self.assertEqual(results, [(section.name, filedict)])

    # TODO Test exceptions in `run`.
