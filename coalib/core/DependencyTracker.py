from itertools import chain

from coalib.core.Graphs import traverse_graph


# TODO Make doctests
class DependencyTracker:
    # TODO docstring here

    def __init__(self):
        self._dependency_dict = {}

    def get_dependants(self, dependency):
        """
        Returns all dependants for the given dependency.

        :param dependency:
            The dependency to retrieve all dependants from.
        :return:
            A set of dependants.
        """
        try:
            return set(self._dependency_dict[dependency])
        except KeyError:
            return set()

    def get_dependencies(self, dependant):
        """
        Returns all dependencies of a given dependant.

        :param dependant:
            The dependant to retrieve all dependencies from.
        :return:
            A set of dependencies.
        """
        return set(
            dependency
            for dependency, dependants in self._dependency_dict.items()
            if dependant in dependants)

    def get_all_dependants(self, dependency):
        """
        Returns a set of all dependants of the given dependency, even not
        directly related ones.

        >>> tracker = DependencyTracker()
        >>> tracker.add(0, 1)
        >>> tracker.add(1, 2)
        >>> tracker.get_all_dependants(0)
        {1, 2}

        :param dependency:
            The dependency to get all dependants for.
        :return:
            A set of dependants.
        """
        dependants = set()

        def append_to_dependants(prev, nxt):
            dependants.add(nxt)

        traverse_graph(
            [dependency],
            lambda node: self._dependency_dict.get(node, frozenset()),
            append_to_dependants)

        return dependants

    def get_all_dependencies(self, dependant):
        """
        Returns a set of all dependencies of the given dependants, even not
        directly related ones.

        >>> tracker = DependencyTracker()
        >>> tracker.add(0, 1)
        >>> tracker.add(1, 2)
        >>> tracker.get_all_dependencies(2)
        {0, 1}

        :param dependant:
            The dependant to get all dependencies for.
        :return:
            A set of dependencies.
        """
        dependencies = set()

        def append_to_dependencies(prev, nxt):
            dependencies.add(nxt)

        traverse_graph(
            [dependant],
            lambda node:
                {dependency
                 for dependency, dependants in self._dependency_dict.items()
                 if node in dependants},
            append_to_dependencies)

        return dependencies

    @property
    def dependants(self):
        """
        Returns a set of all registered dependants.
        """
        return set(chain.from_iterable(self._dependency_dict.values()))

    @property
    def dependencies(self):
        """
        Returns a set of all registered dependencies.
        """
        return set(self._dependency_dict.keys())

    def add(self, dependency, dependant):
        """
        Add a bear-dependency to another bear manually.

        This function does not check for circular dependencies.

        :param dependency:
            The bear that is the dependency.
        :param dependant:
            The bear that is dependent.
        :raises CircularDependencyError:
            Raised when circular dependencies occur.
        """
        if dependency not in self._dependency_dict:
            self._dependency_dict[dependency] = set()

        self._dependency_dict[dependency].add(dependant)

    def resolve(self, dependency):
        """
        When a bear completes this method is called with the instance of that
        bear. The method deletes this bear from the list of dependencies of
        each bear in the dependency dictionary. It returns the bears which
        have all of its dependencies resolved.

        :param dependency:
            The dependency.
        :return:
            Returns a set of dependants whose dependencies were all resolved.
        """
        # Check if dependency has itself dependencies which aren't resolved,
        # these need to be removed too. The ones who instantiate a
        # DependencyTracker are responsible for resolving dependencies in the
        # right order. This operation does not free any dependencies.
        dependencies_to_remove = []
        for tracked_dependency, dependants in self._dependency_dict.items():
            if dependency in dependants:
                dependants.remove(dependency)

                # If dependants set is now empty, schedule dependency for
                # removal from dependency_dict.
                if not dependants:
                    dependencies_to_remove.append(tracked_dependency)

        for tracked_dependency in dependencies_to_remove:
            del self._dependency_dict[tracked_dependency]

        # Now free dependants which do depend on the given dependency.
        possible_freed_dependants = self._dependency_dict.pop(
            dependency, frozenset())
        non_free_dependants = set()

        for possible_freed_dependant in possible_freed_dependants:
            # Check if all dependencies of dependants from above are satisfied.
            # If so, there are no more dependencies for dependant. Thus it's
            # resolved.
            for dependants in self._dependency_dict.values():
                if possible_freed_dependant in dependants:
                    non_free_dependants.add(possible_freed_dependant)
                    break

        # Remaining dependents are officially resolved.
        return possible_freed_dependants - non_free_dependants

    def check_circular_dependencies(self):
        """
        Checks whether there are circular dependency conflicts.

        :raises CircularDependencyError:
            Raised on circular dependency conflicts.
        """
        traverse_graph(
            self._dependency_dict.keys(),
            lambda node: self._dependency_dict.get(node, frozenset()))

    @property
    def all_dependencies_resolved(self):
        return len(self._dependency_dict) == 0
