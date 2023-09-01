
import os
from IR_nodes import *
from graphviz import Digraph


'''
	Creates a visual rendering of the IR graph using graphviz
'''


def render_visual_graph(output_graph_name, root_nodes):

    visual_graph = Digraph()

    for root_node in root_nodes:
        _render_visual_graph(visual_graph, root_node)

    # Create the "Output" folder if it doesn't exist
    output_folder = "out"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save the FSM graph as a file
    output_path = os.path.join(output_folder, output_graph_name)
    visual_graph.format = "png"
    visual_graph.render(output_path, view=False)


def _render_visual_graph(visual_graph, node):
    if node is None:
        return

    for child in node.children:
        if type(node) is AsyncIRGraphNode:
            visual_graph.edge(f"{node.name} {node.id}",
                              f"{child.name} {child.id}", style="dotted")
        elif type(node) is GeneratedBlockIRGraphNode:
            visual_graph.edge(f"{node.name} {node.id}",
                              f"{child.name} {child.id}", style="dashed")
        else:
            visual_graph.edge(f"{node.name} {node.id}",
                              f"{child.name} {child.id}", style="solid")
        _render_visual_graph(visual_graph, child)


'''
	Creates a deep copy of the entire tree under src_node and places it under the dst_node of the dst_graph
'''


def copy_tree(src_node, dst_graph, dst_node):
    dst_graph.pointer = dst_node
    _copy_tree(dst_graph, src_node)


def _copy_tree(dst_graph, node):
    copied_node = copy.copy(node)
    dst_graph.add_node(copied_node)

    if len(node.children) > 1:
        for child in node.children:
            dst_graph.pointer = copied_node
            _copy_tree(dst_graph, child)
    elif len(node.children) == 1:
        _copy_tree(dst_graph, node.children[0])


def remove_duplicates(l):
    return list(set(l))


'''
	Returns the leaf nodes of a graph, including those inside subgraph links. Removes duplicates.
'''


def get_subgraph_leaf_nodes(node):
    leaves = []
    _get_subgraph_leaf_nodes(node, leaves)
    return remove_duplicates(leaves)


def _get_subgraph_leaf_nodes(node, leaves):
    if not node.children:
        leaves.append(node)
        return

    for child in node.children:
        # Enter subgraphs
        if isinstance(child, GeneratedLinkIRGraphNode):
            _get_subgraph_leaf_nodes(child.linked_graph.root_node, leaves)
        else:
            _get_subgraph_leaf_nodes(child, leaves)
