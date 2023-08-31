
from utils.random_util import RandomUtil
from utils.graph_util import *

from IR_nodes import *

import logging


random_util = RandomUtil(123)

# For visual rendering
node_count = 0
'''
################################################
	IR GRAPH
################################################
'''

class IRGraph:
	def __init__(self, root_node=None):
	 
		self.generated_name = random_util.generate_function_name()
	 
		self.root_node = root_node
  
		self.pointer = None
  
	def add_node(self, graph_node):
	 
		global node_count
		# Initialize root node
		if self.root_node is None:
			logging.debug(f"Initializing root node of graph with node {graph_node.name}")
			graph_node.IR_graph = self
			graph_node.id = node_count
			node_count += 1
			self.root_node = graph_node
			self.pointer = self.root_node
			return

		graph_node.IR_graph = self
		graph_node.id = node_count
		node_count += 1
  
		logging.debug(f"Adding node {graph_node.name} {graph_node.id} to parent node {self.pointer.name} {graph_node.id}")
		self.pointer.add_child(graph_node)

		self.pointer = graph_node

	def replace_node(self, old_node, new_node):
		# Replace old_node's parent's reference to this old_node with new_node
		old_node.parent.remove_child(old_node)
		old_node.parent.add_child(new_node)
  
		# Replace old_node's children reference to old_node with new_node
		for child in old_node.children:
			child.parent = new_node
   
		del old_node
  
	def insert_between_nodes(self, parent_node, child_node, new_node):
		# Remove the child_node from parent_node's children list
		parent_node.remove_child(child_node)
		
		# Add new_node as a child of parent_node
		parent_node.add_child(new_node)
		
		# Set new_node as the parent of child_node
		new_node.add_child(child_node)
		
		# Set the IRGraph and id for the new node
		global node_count
		new_node.IR_graph = self
		new_node.id = node_count
		node_count += 1


	def remove_node(self, removed_node):
		removed_node.parent.remove_child(removed_node)

	def get_descendants(self, node):
		children = []
		self._get_descendants(node, children)
		return children
  
	def _get_descendants(self, node, children):
		if not node.children: return
  	
		for child in node.children:
			children.append(child)
			self._get_descendants(child)
   
	def get_leaf_nodes(self, node):
		leaves = []
		self._get_leaf_nodes(node, leaves)
		return leaves

	def _get_leaf_nodes(self, node, leaves):
		if not node.children: 
			leaves.append(node)
			return
  	
		for child in node.children:
			self._get_leaf_nodes(child, leaves)
	 
	def preorder(self, node, visited=None):
		if visited is None:
			visited = []

		if node not in visited:
			visited.append(node)
			yield node
			for child in node.children:
				yield from self.preorder(child, visited)

	def postorder(self, node, visited=None):
		if visited is None:
			visited = []

		if node not in visited:
			visited.append(node)
			for child in node.children:
				yield from self.postorder(child, visited)
			yield node

