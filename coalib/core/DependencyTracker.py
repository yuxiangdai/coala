from collections import defaultdict


class CircularDependencyError(Exception):

    def __init__(self, dependency_circle):
        """
        Creates the CircularDependencyError with a helpful message about the
        dependency.

        :param dependency_circle:
            The sequence of dependencies which form a circle. Should include
            the item that causes the ``CircularDependencyError``.
        """
        Exception.__init__(
            self,
            'Circular dependency detected: ' + ' -> '.join(
                repr(dependency) for dependency in dependency_circle))


class DependencyTracker:

    def __init__(self):
        self.dependency_dict = defaultdict(set)

    def _add_dependency(self, bear, dependant):
        self.dependency_dict[bear].add(dependant)
        self._add_dependency(bear_instance, bear)

    def add(self, dependency, dependant):
        """
        Add a bear-dependency to another bear manually.

        :param dependency:
            The bear that is the dependency.
        :param dependant:
            The bear that is dependent.
        :raises CircularDependencyError:
            Raised when circular dependencies occur.
        """
        self.check_circular_dependency()
        self._add_dependency(dependency, dependant)

    # TODO This method should be removed. Bear dependency creation is highly
    # TODO   interface specific, i.e. when having to different bear instances
    # TODO   of the same bear class, and they have a dependency, then there's
    # TODO   a clash. This can happen for example with 2 sections, with the
    # TODO   same bears but different setups.
    def add_bears_dependencies(self, bears):
        """
        Scans all bears for their dependencies and adds them accordingly to
        this ``DependencyTracker``.

        :param bears:
            Sequence of bears whose dependencies shall be added.
        :raises CircularDependencyError:
            Raised when circular dependencies occur.
        """
        self.check_circular_dependency(bears)
        for bear_instance in bears:
            for bear in bear_instance.BEAR_DEPS:
                self._add_dependency(bear, dependant)

    @staticmethod
    def check_circular_dependency(bears, resolved=None, seen=None):
        # TODO try to use sets.
        if resolved is None:
            resolved = []
        if seen is None:
            seen = []

        for bear in bears:
            if bear in resolved:
                continue

            missing = bear.missing_dependencies(resolved_bears)
            if not missing:
                resolved_bears.append(bear)
                continue

            if bear in seen:
                seen.append(bear)
                raise CircularDependencyError(seen)

            resolved_bears = self.check_circular_dependency(
                missing, resolved_bears, seen + [bear])
            resolved_bears.append(bear)
            seen.remove(
                bear)  # Already resolved, no candidate for circular dep

        return resolved_bears

    def check_circular_dependencies(self):
        # Use a copy of the dependency dict to walk through.
        dependencies = dict(self.dependency_dict)

        # Use path-tracing to find circular dependencies.
        while dependencies:
            path = set()
            # Use also a path-list which supports ordering, so we can present a
            # better exception message that shows the dependency order.
            ordered_path = []

            dependency, dependant = dependencies.popitem()

            path.add(dependency)
            ordered_path.append(dependency)

            while dependant in dependencies:
                if dependant in path:
                    ordered_path.append(path)
                    raise CircularDependencyError(ordered_path)
                else:
                    path.add(dependant)
                    ordered_path.append(dependant)

                dependant = dependencies.pop(dependant)

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
        for tracked_dependency, dependants in self.dependency_dict.items():
            if dependency in dependants:
                dependants.remove(dependency)

                # If dependants set is now empty, schedule dependency2 for
                # removal from dependency_dict.
                if not dependants:
                    dependencies_to_remove.append(tracked_dependency)

        for tracked_dependency in dependencies_to_remove:
            del self.dependency_dict[tracked_dependency]

        # Now free dependants which do depend on the given dependency.
        possible_freed_dependants = self.dependency_dict.pop(dependency, set())
        non_free_dependants = set()

        for possible_freed_dependant in possible_freed_dependants:
            # Check if all dependencies of dependants from above are satisfied.
            # If so, there are no more dependencies for dependant. Thus it's
            # resolved.
            for dependants in self.dependency_dict.values():
                if possible_freed_dependant in dependants:
                    non_free_dependants.add(possible_freed_dependant)
                    break

        # Remaining dependents are officially resolved.
        return possible_freed_dependants - non_free_dependants

    # TODO Make dependency_dict "private"
