import unittest

from coalib.core.Core import initialize_dependencies


# TODO Use real bears
class BearBase:
    def __init__(self, section):
        self.section = section


class BearA(BearBase):
    DEPENDENCIES = set()


class BearB(BearBase):
    DEPENDENCIES = set()


class BearC(BearBase):
    DEPENDENCIES = {BearB}


class BearD(BearBase):
    DEPENDENCIES = {BearC}


class BearE(BearBase):
    DEPENDENCIES = {BearA, BearD}


class CoreTest(unittest.TestCase):
    def test_initialize_dependencies(self):
        bear_e = BearE(object())
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

        self.assertEqual(dependency_tracker.get_dependencies(bear_a), set())

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_d)), 1)
        bear_c = dependency_tracker.get_dependencies(bear_d).pop()
        self.assertIsInstance(bear_c, BearC)

        self.assertEqual(len(dependency_tracker.get_dependencies(bear_c)), 1)
        bear_b = dependency_tracker.get_dependencies(bear_c).pop()
        self.assertIsInstance(bear_b, BearB)

        self.assertEqual(dependency_tracker.get_dependencies(bear_b), set())

        # TODO Test if we preinstantiate some bears, all bears, some bears twice
        # TODO And the case when no dependencies at all occur!
