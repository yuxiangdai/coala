from coalib.core import CircularDependencyError


def traverse_graph(start_nodes, get_successive_nodes,
                   run_on_node=lambda prev, next: None, visited_nodes=None):
    if visited_nodes is None:
        visited_nodes = set()

    next_nodes = set()
    for node in start_nodes:
        if node in visited_nodes:
            raise CircularDependencyError(node)

        for next_node in get_successive_nodes(node):
            run_on_node(node, next_node)
            next_nodes.add(next_node)

    visited_nodes |= set(start_nodes)

    if next_nodes:
        traverse_graph(next_nodes, get_successive_nodes, run_on_node,
                       visited_nodes)

    visited_nodes -= start_nodes
