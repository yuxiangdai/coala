from coalib.core import CircularDependencyError


def traverse_graph(start_nodes, get_successive_nodes,
                   run_on_edge=lambda prev, nxt: None):
    """
    Traverses all edges of a directed acyclic graph once. Detects cyclic graphs
    by raising a ``CircularDependencyError``.

    :param start_nodes:
        The nodes where to start traversing the graph.
    :param get_successive_nodes:
        A callable that takes in a node and returns an iterable of nodes to
        traverse next.
    :param run_on_edge:
        A callable that is run on each edge during traversing. Takes in two
        parameters, the previous- and next-node which form an edge. The default
        is an empty function.
    :raises CircularDependencyError:
        Raised when the graph is cyclic.
    """
    path = set()
    visited_nodes = set()

    def visit(node):
        for subnode in get_successive_nodes(node):
            if subnode in path:
                raise CircularDependencyError(subnode)

            run_on_edge(node, subnode)

            if subnode in visited_nodes:
                continue

            visited_nodes.add(subnode)
            path.add(subnode)

            visit(subnode)

            path.remove(subnode)

    for node in start_nodes:
        if node not in visited_nodes:
            visited_nodes.add(node)
            path.add(node)

            visit(node)

            path.remove(node)
