import os

import tests.cases as cases

import luaparser
import luaparser.ast as ast
import luaparser.astnodes as astnodes
from luaparser.astnodes import *
from luaparser.astnodes import Node

from utils.random_util import RandomUtil

from graphviz import Digraph

from typing import List
import coloredlogs, logging

import copy

# windows only
if os.name == 'nt':
	os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'
 
os.environ["COLOREDLOGS_LOG_FORMAT"] ='[%(hostname)s] %(funcName)s :: %(levelname)s :: %(message)s'

coloredlogs.install(level='DEBUG')

random_util = RandomUtil(123)

# For visual rendering
node_count = 0

'''
	Converts lua code to an event-driven finite state machine (substitute for coroutines)
	- Splits functions into multiple functions, seperated by async events
	- Async events defined by await(foo()) calls
	- Handles events inside conditional blocks

	Limitations:
	- No recursion
 
	TODO:
	- Error handling on invalid syntax
	- Error handling on detected recursion
	- Function closure (function inside function)
	- Loops
 	- Async assignments
	- Gotos and labels
 	- Objects/Methods
	- Track global table of async functions
	- Error handling on missing await()
	- Update local and global assignments/references to global table
'''


class IRGraphNode:
	def __init__(self, lua_node):
		self.IR_graph = None
		self.id = -1
		self.lua_node = lua_node
		if lua_node:
			self.name = lua_node._name
		self.name_extra = ''
		self.parent = None
		self.children = []
		self.contains_async = False

	def __copy__(self):
		cls = self.__class__
		result = cls.__new__(cls)
		result.IR_graph = None
		result.id = -1
		result.lua_node = self.lua_node
		result.name = self.name
		result.parent = None
		result.children = []
		return result

	def add_child(self, child):
		child.parent = self
		self.children.append(child)
  
	def add_children(self, children):
		for child in children:
			child.parent = self
		self.children.extend(children)
   
	def remove_child(self, removed_child):
		self.children = [child for child in self.children if child is not removed_child]
   
	def remove_children(self, removed_children):
		self.children = [child for child in self.children if child not in removed_children]


'''
################################################
	REGULAR IR NODES
################################################
'''

'''
	Regular graph nodes are any sort of exeuction that does not introduce differing levels of heirarchy or asynchronous calls
	and do not require any modification
'''
class RegularIRGraphNode(IRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

class FunctionIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
  
class LocalFunctionIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Local assignments 
'''
class LocalAssignIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Global assignments
'''
class GlobalAssignIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
  
'''
	Semicolons
'''
class SemicolonIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
 
'''
	Do-end blocks are typically used to introduce stricter scoping, and they do introduce differing levels of heirarchy--
	but given that all variables will be converted to global variables anyways it doesn't matter.
'''
class DoIRGraphNode(RegularIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)


  
'''
################################################
	ASYNC IR NODES
################################################
'''

'''
	Asynchronous graph nodes
'''
class AsyncIRGraphNode(IRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
		self.name = lua_node._name + ' (A)'
		self.contains_async = True

'''
	Asynchronous function calling
'''
class AsyncCallIRGraphNode(AsyncIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Asynchronous assignments
'''
class AsyncAssignIRGraphNode(AsyncIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)


'''
################################################
	CONTROL STRUCTURES IR NODES
################################################
'''

class ControlStructureIRGraphNode(IRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Conditional graph nodes (children to generated branch nodes)
'''
class ConditionalIRGraphNode(ControlStructureIRGraphNode):
	def __init__(self, lua_node, name=""):
		super().__init__(lua_node)
		if name != "": self.name = name

class BreakIRGraphNode(ControlStructureIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
  
class ReturnIRGraphNode(ControlStructureIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

class GotoIRGraphNode(ControlStructureIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
  
class LabelIRGraphNode(ControlStructureIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

  
'''
################################################
	LOOP IR NODES
################################################
'''
class LoopIRGraphNode(IRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)


'''
	Lua first tests the while condition; if the condition is false, then the loop ends; 
	otherwise, Lua executes the body of the loop and repeats the process.
'''
class WhileIRGraphNode(LoopIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	A repeat-until statement repeats its body until its condition is true. 
	The test is done after the body, so the body is always executed at least once.
'''
class RepeatIRGraphNode(LoopIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	The generic for loop allows you to traverse all values returned by an iterator function.
'''  
class ForinIRGraphNode(LoopIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
'''
	The numeric for loop works as usual. 
	All three expressions in the declaration of the for loop are evaluated once, before the loop starts. 
'''
class FornumIRGraphNode(LoopIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
################################################
	COMPILATION GENERATED IR NODES
################################################
'''

class GeneratedIRGraphNode(IRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)


'''
	Helper node for statements with bodies
'''
class GeneratedBlockIRGraphNode(IRGraphNode):
	def __init__(self, lua_node=None):
		super().__init__(lua_node)
		self.name = "Block (G)"

'''
	Links IR graphs together, dst_node will be the root node of another IR graph
'''
class GeneratedLinkIRGraphNode(GeneratedIRGraphNode):
	def __init__(self, linked_graph):
		super().__init__(lua_node=None)
		self.name = "Link " + linked_graph.generated_name[5:10] + " (G)" 
		self.name_extra = linked_graph.generated_name[4:10]
		self.linked_graph = linked_graph 
		if self.linked_graph is None:
			print("here")
			exit()
'''
	Placeholder for a new function node
'''
class GeneratedFunctionIRGraphNode(GeneratedIRGraphNode):
	def __init__(self, generated_function_name):
		super().__init__(lua_node=None)
		self.generated_function_name = generated_function_name
		self.name = "Function " + generated_function_name[5:10] + " (G)"
		self.name_extra = generated_function_name[4:10]
  
'''
	Intermediate reprsentation for conditionals. This node will contain each elseif/else statement.
'''
class GeneratedBranchIRGraphNode(GeneratedIRGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
		self.name = 'Branch (G)'
		self.else_statement_present = False
'''
	Placeholder for new else node
'''
class GeneratedConditionalElseIRGraphNode(GeneratedIRGraphNode):
	def __init__(self):
		super().__init__(lua_node=None)
		self.name = "Else (G)"
  
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
  
	def insert_parent_node(self, node, new_parent):
		pass

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
    if node is None: return

    for child in node.children:
        if type(node) is AsyncIRGraphNode:
            visual_graph.edge(f"{node.name} {node.id}", f"{child.name} {child.id}", style="dotted")
        elif type(node) is GeneratedBlockIRGraphNode:
            visual_graph.edge(f"{node.name} {node.id}", f"{child.name} {child.id}", style="dashed") 
        else:
            visual_graph.edge(f"{node.name} {node.id}", f"{child.name} {child.id}", style="solid")
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

'''
################################################
	TRANSLATOR
################################################
'''

class Translator:
	def __init__(self, source_lua_root_node, render_visual_graph):
		self.source_lua_root_node = source_lua_root_node 
		self.render_visual_graph = render_visual_graph
  
		# Graphs
		self.IR_graph = IRGraph() 
		self.exeuction_IR_graphs = []
		

		# Main function tracking	
		self.main_function_name = None
		self.function_count = 0
		self.inside_main_function = False
  
		# Variable reference tracking
		self.variable_refs = {}

	'''
	################################################
		IR TRANSLATION	
	################################################
	'''
	'''
	3. Construct Execution Graph: 
 		- Separate async statements:
		-- Find async node (x), add children of (x) to new IR graph, replace child of (x) with link to new IR graph
		- Linearize Branches:
		-- Find node (x) with a branch child, add other children of (x) to a new IR graph, then append it to the end 
		of each execution path of the branch child as a link node.
		-- If there is no else statement present, create one

	'''
	'''
	Translating is done as follows:
	1. Build/Expand IR graph:
		- Build the Intermediate Representation (IR) graph tree
		-- 1a. (Build) Travsering from the root, find all regular, conditional and loop nodes and add them to the graph linearly 
		(without going into the branches or loops)
		-- 1b. (Expand) For each node with a block, enter the block
  		-- 1c. Mark whether the block contains an async call/assignment
    	-- 1d. goto 1a
	x. Check for recusion
		- Make sure no functions recurse. If they do, then throw an error
    x. Mark async blocks
		- Find blocks that contain async statements and mark them for later
	x. Modify Assignments: 
		- Change local assignments to global assignments
		- Track all variables in variable reference table
	x. Modify branches:
		- Unpack assignments in conditionals
		- If there is no else statement present, create one and put the post execution tree under the new else node
	4. Construct Execution Graphs: 
		- Linearize:
		-- Find node (x) with a branch child, add other children of (x) to a new IR graph, then append it to the end 
		of each execution path of the branch child as a link node.
		- Separate:
		-- Find async node (x), add children of (x) to new IR graph, replace child of (x) with link to new IR graph
	x. Extract functions:
		- Extract and link functions together
	x. Construct AST:
		- Secrete a new lua AST
	'''
	def translate(self):
		# Stage 1
		# Build the graph tree 
  
		logging.info(f"Building IR graph from Lua source")
		self.build_IR_graph(self.source_lua_root_node)
		if self.render_visual_graph: 
			render_visual_graph(output_graph_name="IR_graph", root_nodes=[self.IR_graph.root_node])


		logging.info(f"Expanding IR graph")
		self.expand_nodes(self.IR_graph.root_node)
		if self.render_visual_graph: 
			render_visual_graph(output_graph_name="Expanded_IR_graph", root_nodes=[self.IR_graph.root_node])

		# logging.info(f"Checking for recursion")
		# try:
		# 	self.check_for_recursion(self.IR_graph.root_node)
		# except Exception():
		# 	logging.error("Recursion detected")

		
		# logging.info("Modifying assignments to global assignments")
		# # self.modify_assignments(self.IR_graph.root_node)
		# if self.render_visual_graph:
		# 	render_visual_graph(output_graph_name="Modified_assignments_IR_graph", root_nodes=[self.IR_graph.root_node])

		# logging.info("Updating assignment references to global references")
		# # self.update_assignment_references(self.IR_graph.root_node)
		# if self.render_visual_graph:
		# 	render_visual_graph(output_graph_name="Modified_assignments_IR_graph", root_nodes=[self.IR_graph.root_node])
		
		logging.info(f"Linearizing branches into exeuction graphs")
		self.linearize_branches()
		if self.render_visual_graph: 
			root_nodes = [graph.root_node for graph in self.exeuction_IR_graphs]
			root_nodes.append(self.IR_graph.root_node)
			render_visual_graph(output_graph_name="linearized_branches_IR_graphs", root_nodes=root_nodes)
		
		logging.info(f"Separating async statements into exeuction graphs")
		self.separate_async_statements()
		if self.render_visual_graph: 
			root_nodes = [graph.root_node for graph in self.exeuction_IR_graphs]
			root_nodes.append(self.IR_graph.root_node)
			render_visual_graph(output_graph_name="seperated_async_IR_graphs", root_nodes=root_nodes)
		logging.info(f"Constructing new AST")
		self.construct_ast()


	def build_IR_graph(self, node):
		# First collect regular/async statements, branches and loops (without entering)
		logging.debug("Collecting nodes")	
		self.visit(node)


	# Enter the bodies of if statements and loops
	def expand_nodes(self, node):
		print(node)
		print(type(node))
		# If the node is a branch, expand the children
		if isinstance(node, GeneratedBranchIRGraphNode):
			# The lua node for the branch holds the "if" lua node
			# Each subsequent conditional is found in the 'orelse' field
			if_node = node.lua_node

			# Find all conditional branches
			conditional_nodes = [ConditionalIRGraphNode(lua_node=if_node)]
			lookahead_node = if_node.orelse
			while(isinstance(lookahead_node, luaparser.astnodes.ElseIf)):
				logging.debug(f"Found ElseIf")
				conditional_nodes.append(ConditionalIRGraphNode(lua_node=lookahead_node))
				lookahead_node = lookahead_node.orelse
			if(lookahead_node is not None):
				# Else statement is of type list<Statement>
				logging.debug(f"Found Else")
				node.else_statement_present = True
				conditional_nodes.append(ConditionalIRGraphNode(lua_node=lookahead_node, name="Else"))

			
			# Add block for body
			body_block_node = GeneratedBlockIRGraphNode()
			self.IR_graph.pointer = node
			self.IR_graph.add_node(body_block_node)
			for conditional_node in conditional_nodes:
				self.IR_graph.pointer = body_block_node
				self.IR_graph.add_node(conditional_node)
	
			# Visit each of the conditionals in the body
			for conditional_node in body_block_node.children:
				self.IR_graph.pointer = conditional_node
				self.visit(conditional_node.lua_node.body)

		# If the node is a loop, expand
		elif isinstance(node, LoopIRGraphNode):
			self.IR_graph.pointer = node
			if isinstance(node, FornumIRGraphNode):
				self.IR_graph.add_node(GeneratedBlockIRGraphNode())
				self.visit(node.lua_node.body)
			if isinstance(node, ForinIRGraphNode):
				self.IR_graph.add_node(GeneratedBlockIRGraphNode())
				self.visit(node.lua_node.body)
			if isinstance(node, WhileIRGraphNode):
				self.IR_graph.add_node(GeneratedBlockIRGraphNode())
				self.visit(node.lua_node.body)
			if isinstance(node, RepeatIRGraphNode):
				self.IR_graph.add_node(GeneratedBlockIRGraphNode())
				self.visit(node.lua_node.body)

		# Expand each child	
		for child in node.children:
			self.expand_nodes(child)

	

	# def modify_assignments(self, node):
	# 	# If the node is an assignment node
	# 	if isinstance(node, RegularAssignIRGraphNode, LocalAssignIRGraphNode):
	# 		# Construct the new lua node
	# 		global_assign_lua_node = self.construct_global_assign_lua_node()
   			
    #   		# Create a new GlobalAssignIRGraphNode
	# 		newAssignNode = GlobalAssignIRGraphNode()
	# 		node.__class__ = GlobalAssignIRGraphNode
	# 		# Add the variables to the modified_vars set
	# 		for target in node.lua_node.targets:
	# 			if isinstance(target, astnodes.Name):
	# 				self.modified_vars.add(target.id)

	# 	# Visit the child nodes
	# 	for child in node.children:
	# 		self.modify_assignments(child)

	# def update_references(self, node):
	# 	# If the node is an expression node that references a variable
	# 	if isinstance(node, RegularIRGraphNode) and isinstance(node.lua_node, astnodes.Name):
	# 		# If the variable has been changed to a global variable
	# 		if node.lua_node.id in self.modified_vars:
	# 			# Change the reference to a global reference
	# 			# This will require creating a new node type or modifying the existing node
	# 			# For example, you might add an attribute to the Name node to indicate that it's a global reference
	# 			node.lua_node.is_global = True

	# 	# Visit the child nodes
	# 	for child in node.children:
	# 		self.update_references(child)

	def linearize_branches(self):
		traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)
  
		for node in traversal_order:
   			# Check if node have branch as children
			branch_present = False
			branch_node = None
			for child in node.children:
				if isinstance(child, GeneratedBranchIRGraphNode):
					branch_present = True
					branch_node = child
    

			# The post exeuction tree are nodes that execute after the nodes in the branch
			post_exeuction_tree = None

			if branch_present:
				block_node = None
				# Find the post exeuction tree (if present)
				logging.debug(f"Found Branch {branch_node.id}")
				for child in branch_node.children:
					if not isinstance(child, GeneratedBlockIRGraphNode):
						post_exeuction_tree = child
					elif isinstance(child, GeneratedBlockIRGraphNode):
						block_node = child
				
				# Continue if there is no post exeuction tree (not present or branch has already been linearized)
				if post_exeuction_tree is None:
					continue
 
				logging.debug(f"Found post execution tree {post_exeuction_tree.name} {post_exeuction_tree.id}")
				
  
				# '''
				# Modify Branches:
				# - Find Nonterminal Conditional Branches (NCBs), that is branches that do not contain an else statement.
				# 	-- When linearizing, code that is executed after the if statement is appended to each conditional in the branch. This creates a problem in the following case:
				# 	* The code is linearized
				# 	* There is code after the branch (post exeuction tree)
				# 	* The branch does not contain an else statement
				# 	* All conditionals of the branch evaluate to false
				# 	The linearized post exeuction tree will never be executed. We can fix this by copying the tree to a new artificially created
				# 	'else' conditional node under the NCB. 
				# '''

				# if not branch_node.else_statement_present:
				# 	logging.debug(f"Branch {branch_node.id} does not have an else statement, creating one")
				# 	# Construct a placeholder node
				# 	placeholder_else_node = GeneratedConditionalElseIRGraphNode()
				# 	self.IR_graph.pointer = branch_node
				# 	self.IR_graph.add_node(placeholder_else_node)
				
				# Find all leaf nodes, including those inside linked subgraphs
				leaf_nodes = get_subgraph_leaf_nodes(block_node)

				# TODO: Why was this here?
				# Remove post_execution_tree from leaf nodes
				# leaf_nodes = [node for node in leaf_nodes if node is not post_exeuction_tree]

				# Create a new IR graph
				exeuction_IR_graph = IRGraph()

				# Append a new function as the root node
				placeholder_function = GeneratedFunctionIRGraphNode(generated_function_name=exeuction_IR_graph.generated_name)
				exeuction_IR_graph.add_node(placeholder_function)
				logging.debug(f"Constructed new IR graph with root node {exeuction_IR_graph.root_node.name} {exeuction_IR_graph.root_node.id}")

				# Copy the post execution tree to the new IR graph
				logging.debug(f"Copying tree from source node {post_exeuction_tree.name} {post_exeuction_tree.id} to graph {exeuction_IR_graph.generated_name[4:10]} at parent node {exeuction_IR_graph.pointer.name} {exeuction_IR_graph.pointer.id}")
				copy_tree(src_node=post_exeuction_tree, dst_graph=exeuction_IR_graph, dst_node=exeuction_IR_graph.pointer)
				self.exeuction_IR_graphs.append(exeuction_IR_graph)	

				# Add a link to thew new IR graph to each of the leaf nodes
				for leaf_node in leaf_nodes:
					# Find which IR graph the leaf node belongs to
					IR_graph = leaf_node.IR_graph
					# Add link to execution graph
					IR_graph.pointer = leaf_node
					logging.debug(f"Adding link to leaf node {leaf_node.name} {leaf_node.id}")
					IR_graph.add_node(GeneratedLinkIRGraphNode(exeuction_IR_graph))
   
				# Remove the post execution tree from the main IR graph
				self.IR_graph.remove_node(post_exeuction_tree)

				# Reset the traversal order
				traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)

	def separate_async_statements(self):
		traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)
  
		for node in traversal_order:
			if isinstance(node, AsyncIRGraphNode):
			
				# Continue if async node has no children
				if not node.children: continue
    
				# Node should have only one child
				if len(node.children) > 1:
					logging.error("Async node has more than 1 child")

				# Get child of async node
				async_node_child = node.children[0]

				# Create a new IR graph
				exeuction_IR_graph = IRGraph()

				# Append a placeholder function to the new graph as the root node
				placeholder_function = GeneratedFunctionIRGraphNode(generated_function_name=exeuction_IR_graph.generated_name)	
				exeuction_IR_graph.add_node(placeholder_function)
    
				# Copy the child tree of the async node to the new graph			
				copy_tree(src_node=async_node_child, dst_graph=exeuction_IR_graph, dst_node=exeuction_IR_graph.pointer)
				logging.debug(f"Constructed new IR graph with root node {exeuction_IR_graph.root_node.name} {exeuction_IR_graph.root_node.id}")
				self.exeuction_IR_graphs.append(exeuction_IR_graph)
    
				# Remove async node children from main graph
				self.IR_graph.remove_node(async_node_child)
    
				# Add a link from the main graph to the new IR graph
				previous_pointer = self.IR_graph.pointer
				self.IR_graph.pointer = node
				self.IR_graph.add_node(GeneratedLinkIRGraphNode(exeuction_IR_graph))
				self.IR_graph.pointer = previous_pointer
    
				# Reset traversal order
				traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)

	def construct_ast(self):
		pass

	'''
	################################################
		LUA AST NODE BUILDERS	
	################################################
	'''

	'''
		Else nodes are list<Statement>
  	'''
	def construct_else_lua_node():
		pass
		# return astnodes.
 
	def construct_global_assign_lua_node():
		pass
	
	def construct_function_lua_node():
		pass

	'''
	################################################
		LUA AST NODE VISITERS
	################################################
	'''
	'''
		---------------------------------------------------------------------------------------------------
		Call sorting
		---------------------------------------------------------------------------------------------------
 	'''
	def visit(self, node):
		method = 'visit_' + node.__class__.__name__
		# get correct visit function
		visitor = getattr(self, method, self.generic_visit)
		# call visit function with current node
		return visitor(node)

	def generic_visit(self, node):
		if isinstance(node, list):
			for item in node:
				self.visit(item)
		elif isinstance(node, Node):
			logging.debug(f"Generic visit {node._name}")
			# visit all object public attributes:
			children = [
				attr for attr in node.__dict__.keys() if not attr.startswith("_")
			]
			for child in children:
				self.visit(node.__dict__[child])

	'''
		---------------------------------------------------------------------------------------------------
		Regular nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Assign(self, node):
		self.IR_graph.add_node(GlobalAssignIRGraphNode(lua_node=node))

	'''
		Because of the execution environment, all local assignements will be converted to global assignments
		TODO: Use factorio global table?
	'''
	def visit_LocalAssign(self, node):
		self.IR_graph.add_node(LocalAssignIRGraphNode(lua_node=node))
	
	def visit_SemiColon(self, node):
		self.IR_graph.add_node(SemicolonIRGraphNode(lua_node=node))

	def visit_Do(self, node):
		self.IR_graph.add_node(DoIRGraphNode(lua_node=node))
	'''
		---------------------------------------------------------------------------------------------------
		Loop nodes
		---------------------------------------------------------------------------------------------------
 	'''
 
	def visit_While(self, node):
		self.IR_graph.add_node(WhileIRGraphNode(lua_node=node))

	def visit_Forin(self, node):
		self.IR_graph.add_node(ForinIRGraphNode(lua_node=node))

	def visit_Fornum(self, node):
		self.IR_graph.add_node(FornumIRGraphNode(lua_node=node))

	def visit_Repeat(self, node):
		self.IR_graph.add_node(RepeatIRGraphNode(lua_node=node))
	
	def visit_Break(self, node):
		self.IR_graph.add_node(BreakIRGraphNode(lua_node=node))
 
	def visit_Return(self, node):
		self.IR_graph.add_node(ReturnIRGraphNode(lua_node=node))
	'''
		---------------------------------------------------------------------------------------------------
		Conditional nodes
		---------------------------------------------------------------------------------------------------
 	'''
	# def visit_ElseIf(self, node):
	# 	logging.debug(f"Visited ElseIf")
	# 	self.IR_graph.add_node(ConditionalIRGraphNode(lua_node=node))
  
		# self.visit(node.body)
		# self.visit(node.orelse)

	def visit_If(self, node):
		self.IR_graph.add_node(GeneratedBranchIRGraphNode(lua_node=node))


  
	'''
		---------------------------------------------------------------------------------------------------
		Function nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Function(self, node):
		logging.debug(f"Visited {node.name.id} with arguments {node.args}")
		if self.function_count > 0:
			raise Exception("Error: More than one function defined. Scripts should only contain one function definition.")
	
		self.function_count += 1
		self.main_function_name = node.name.id
		logging.info(f"Found main function {self.main_function_name}")

		# We are now traversing inside the main function
		self.inside_main_function = True
  
		self.IR_graph.add_node(FunctionIRGraphNode(lua_node=node))

		self.visit(node.body)

	def visit_LocalFunction(self, node):
		# TODO: Just change function to not be local
		raise Exception("Error: Function must not be a local function")


	def visit_Call(self, node):
		logging.debug(f"Visited {node.func.id} with arguments {node.args}")
		# Find await() calls
		if node.func.id == 'await':
			logging.info(f"Await call found. Function: {node.args[0].func.id}")
			self.IR_graph.add_node(AsyncIRGraphNode(lua_node=node))
		else:
			# Regular function call
			self.IR_graph.add_node(RegularIRGraphNode(lua_node=node))

	'''
		---------------------------------------------------------------------------------------------------
		Unsupported nodes	
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Label(self, node):
		self.IR_graph.add_node(LabelIRGraphNode)

	def visit_Goto(self, node):
		self.IR_graph.add_node(GotoIRGraphNode)

	def visit_Invoke(self, node):
		raise Exception("Error: Invoking object methods is not supported.")

	def visit_Method(self, node):
		raise Exception("Error: Defining object methods is not supported.")




# Convert the source code to an AST
source_lua_root_node = ast.parse(cases.source_code_5)

#print(ast.to_pretty_str(tree))
# Create FSM graph

# Translate
translator = Translator(source_lua_root_node, render_visual_graph=True)
translator.translate()



