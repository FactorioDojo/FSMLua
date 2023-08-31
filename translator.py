import os

import tests.cases as cases
import luaparser.ast as ast
import luaparser.astnodes as astnodes

from utils.random_util import RandomUtil
from utils.graph_util import *

from IR_graph import IRGraph
from IR_nodes import *


from typing import List
import coloredlogs, logging

# windows only
if os.name == 'nt':
	os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'
 
os.environ["COLOREDLOGS_LOG_FORMAT"] ='[%(hostname)s] %(funcName)s :: %(levelname)s :: %(message)s'

coloredlogs.install(level='DEBUG')



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

'''
	Constants
'''
GLOBAL_EVENT_PTR_TABLE_NAME = 'global.event_ptrs'


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
		self.exeuction_IR_graphs = [self.IR_graph]
	
		# Links
		self.links = []

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
	x. Construct Execution Graphs: 
		- Linearize:
		-- Find node (x) with a branch child, add other children of (x) to a new IR graph, then append it to the end 
		of each execution path of the branch child as a link node.
		- Separate:
		-- Find async node (x), add children of (x) to new IR graph, replace child of (x) with link to new IR graph
	x. Extract functions:
		- Extract and link functions together
	x. Insert event pointers:
		- For each async node and its following link, insert a node that will set the event pointer before the async node
	x. Construct AST headers:
		- Secrete a new lua AST
	x. Construct full AST
		- Secrete the full lua AST
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
			# root_nodes.append(self.IR_graph.root_node)
			render_visual_graph(output_graph_name="linearized_branches_IR_graphs", root_nodes=root_nodes)
		
		logging.info(f"Separating async statements into exeuction graphs")
		self.separate_async_statements()
		if self.render_visual_graph: 
			root_nodes = [graph.root_node for graph in self.exeuction_IR_graphs]
			# root_nodes.append(self.IR_graph.root_node)
			render_visual_graph(output_graph_name="seperated_async_IR_graphs", root_nodes=root_nodes)
  

		logging.info(f"Inserting event pointers")
		self.insert_event_pointers()
		if self.render_visual_graph: 
			root_nodes = [graph.root_node for graph in self.exeuction_IR_graphs]
			# root_nodes.append(self.IR_graph.root_node)
			render_visual_graph(output_graph_name="event_ptrs_IR_graphs", root_nodes=root_nodes)
  
	
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
			while(isinstance(lookahead_node, astnodes.ElseIf)):
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
					link_node = GeneratedLinkIRGraphNode(exeuction_IR_graph, async_link=False)
					IR_graph.add_node(link_node)
	 
					# Track link node
					self.links.append((link_node, exeuction_IR_graph))
   
				# Remove the post execution tree from the main IR graph
				self.IR_graph.remove_node(post_exeuction_tree)

				# Reset the traversal order
				traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)

	def separate_async_statements(self):
		for IR_graph in self.exeuction_IR_graphs:
			traversal_order = IR_graph.postorder(IR_graph.root_node)
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
					link_node = GeneratedLinkIRGraphNode(exeuction_IR_graph, async_link=True)
					self.IR_graph.add_node(link_node)
					self.IR_graph.pointer = previous_pointer
		
					# Track link node
					self.links.append((link_node, exeuction_IR_graph))
		
					# Reset traversal order
					traversal_order = self.IR_graph.postorder(self.IR_graph.root_node)

	def insert_event_pointers(self):
		for IR_graph in self.exeuction_IR_graphs:
			traversal_order = IR_graph.preorder(IR_graph.root_node)
			for node in traversal_order:
				if isinstance(node, GeneratedLinkIRGraphNode):
					if node.async_link:
						# Create a new GeneratedSetEventPointerNode with pointer equal to the generated link name
						set_event_pointer_node = GeneratedSetEventPointerNode(node.generated_link_name)
						
						# Get the parent node of the GeneratedLinkIRGraphNode
						parent_node = node.parent				
	
						# Get the grandparent node of the GeneratedLinkIRGraphNode
						grandparent_node = parent_node.parent

						if parent_node and grandparent_node:
							# Insert the GeneratedSetEventPointerNode between the parent and the GeneratedLinkIRGraphNode
							self.IR_graph.insert_between_nodes(grandparent_node, parent_node, set_event_pointer_node)
				
							# Reset traversal order
							traversal_order = self.IR_graph.preorder(self.IR_graph.root_node)


	def construct_ast(self):
		script_body = []	
		script_body_node = astnodes.Block(script_body)
		script_chunk_node = astnodes.Chunk(script_body_node)
  
		event_ptrs = self.construct_event_ptrs(script_body)
		for ptr in event_ptrs:
			print(ast.to_lua_source(ptr))

	'''
		Constructs the event ptr table. i.e
		global.event_ptrs['A_event'] = 'B_event'

		async Call (A) -> Link (A). The link needs to insert a node above call setting the event ptr.
		Any links that are not async should just be function calls
  
  
	global.event_ptrs['doThing'] = A_event

 	'''
	def construct_event_ptrs(self, script_body):
		event_ptrs = []
		for link, graph in self.links:
			if link.async_link:
				event_ptr_assignment_node = \
					astnodes.Assign(
					targets=[
						astnodes.Index(
							idx=astnodes.String(
								s=link.generated_link_name
							),
							value=astnodes.Name(GLOBAL_EVENT_PTR_TABLE_NAME),
							notation=astnodes.IndexNotation.SQUARE,
						)
					],
					values=[astnodes.Name(graph.root_node.generated_function_name)],
				)

				event_ptrs.append(event_ptr_assignment_node)
		return event_ptrs

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

	def construct_event_pointer_assignment():
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
		elif isinstance(node, astnodes.Node):
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



