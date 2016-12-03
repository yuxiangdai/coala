import unittest

from coalib.core import CircularDependencyError
from coalib.core import DependencyTracker


class DependencyTrackerTest(unittest.TestCase):
    def test_check_circular_dependencies(self):
        uut = DependencyTracker()
        uut.add(0, 1)
        uut.add(1, 2)

        uut.check_circular_dependencies()

        uut.add(2, 0)

        with self.assertRaises(CircularDependencyError):
            uut.check_circular_dependencies()

    def test_resolve(self):
        uut = DependencyTracker()
        uut.add(0, 1)
        uut.add(0, 2)
        uut.add(0, 3)
        uut.add(4, 5)
        uut.add(6, 0)

        self.assertEqual(uut.resolve(0), {1, 2, 3})
        # Dependants already resolved.
        self.assertEqual(uut.resolve(0), set())

        # Though 0 had a dependency, it was still forcefully resolved.
        self.assertEqual(uut.resolve(6), set())

        # Let's re-add a dependency for 0.
        uut.add(0, 1)
        self.assertEqual(uut.resolve(0), {1})

    def test_dependencies_resolved(self):
        uut = DependencyTracker()

        self.assertTrue(uut.dependencies_resolved)

        uut.add(0, 1)

        self.assertFalse(uut.dependencies_resolved)

        uut.resolve(0)

        self.assertTrue(uut.dependencies_resolved)
