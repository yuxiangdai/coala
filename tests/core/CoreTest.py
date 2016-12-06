import unittest

from coalib.core import initialize_dependencies


class BearA:
    DEPENDENCIES = set()


class BearB:
    DEPENDENCIES = set()


class BearC:
    DEPENDENCIES = {BearB}


class BearD:
    DEPENDENCIES = {BearC}


class BearE:
    DEPENDENCIES = {BearA, BearD}


class CoreTest(unittest.TestCase):
    if __name__ == '__main__':
        def test_initialize_dependencies(self):
            bear_e = BearE()
            dependency_tracker = initialize_dependencies({bear_e})

            self.assertEqual(len(dependency_tracker.get_dependants(bear_e)), 2)
            self.assertTrue(any(isinstance(bear, BearA) for bear in
                                dependency_tracker.get_dependants(bear_e)))
            self.assertTrue(any(isinstance(bear, BearD) for bear in
                                dependency_tracker.get_dependants(bear_e)))

            bear_a = next(
                bear for bear in dependency_tracker.get_dependants(bear_e)
                if isinstance(bear, BearA))
            bear_d = next(
                bear for bear in dependency_tracker.get_dependants(bear_e)
                if isinstance(bear, BearD))

            self.assertEqual(dependency_tracker.get_dependants(bear_a), set())

            self.assertEqual(len(dependency_tracker.get_dependants(bear_d)), 1)
            bear_c = dependency_tracker.get_dependants(bear_d).pop()
            self.assertEqual(isinstance(bear_c, BearC))

            self.assertEqual(len(dependency_tracker.get_dependants(bear_c)), 1)
            bear_b = dependency_tracker.get_dependants(bear_c).pop()
            self.assertEqual(isinstance(bear_b, BearB))

            self.assertEqual(dependency_tracker.get_dependants(bear_b), set())

            # TODO Test if we preinstantiate some bears, all bears, some bears twice
