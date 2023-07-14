import os

import luaparser
import luaparser.ast as ast
from luaparser.astnodes import *
from luaparser.astnodes import Node

from graphviz import Digraph

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
	- Gotos and labels are not supported
	- Objects/Methods are not supported
	- Must track global table of async functions
 
	TODO:
	- Loops
 	- Async assignments
	
'''


class GraphNode:
	def __init__(self, lua_node):
		self.id = id
		self.lua_node = lua_node
		if lua_node:
			self.name = lua_node._name
		self.parent = None
		self.children = []


	def add_child(self, child):
		child.parent = self
		self.children.append(child)
  
	def add_children(self, children):
		for child in children:
			child.parent = self
		self.children.extend(children)
   
	def remove_children(self, removed_children):
		self.children = [child for child in self.children if child not in removed_children]


'''
	Regular graph nodes are any sort of exeuction that does not introduce differing levels of heirarchy or asynchronous calls
'''
class RegularGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''

'''
class LocalAssignGraphNode(RegularGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Regular graph nodes are any sort of exeuction that does not introduce differing levels of heirarchy or asynchronous calls
'''
class GlobalAssignGraphNode(RegularGraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)


'''
	Asynchronous function calls. 
'''
class AsyncGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)
		self.name = '(async) ' + lua_node._name 

'''
	Conditional graph nodes contain all statements related to an if statement.
'''
class ConditionalGraphNode(GraphNode):
	def __init__(self, lua_node, name=""):
		super().__init__(lua_node)
		if name != "": self.name = name
	
class LoopGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

'''
	Intermediate reprsentation for conditionals. This node will contain each elseif/else statement.
'''
class BranchGraphNode(GraphNode):
	def __init__(self, else_statement_present):
		super().__init__(lua_node=None)
		self.id = id
		self.name = 'Branch'
		self.else_statement_present = else_statement_present
  

  
   
class IRGraph:
	def __init__(self, translator):
		self.translator = translator
		self.visual_graph = Digraph()
  
		self.root_node = None
		self.pointer = None
  
		self.node_count = 0
  

  
	def add_node(self, graph_node):
	 
		# Initialize root node
		if self.root_node is None:
			logging.debug(f"Initializing root node of graph with node {graph_node.name}")
			graph_node.id = self.node_count
			self.node_count += 1
			self.root_node = graph_node
			self.pointer = self.root_node
			return

		graph_node.id = self.node_count
		self.node_count += 1
  
		logging.debug(f"Adding node {graph_node.name} to parent node {self.pointer.name}")
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

	def get_descendants(self, node):
		children = []
		return self._get_descendants(node, children)
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
			self._get_leaf_nodes(self, child, leaves)
	 
	def render_visual_graph(self, output_graph_name, node=None):
  
		self.visual_graph = Digraph()
		
		if node is None: node = self.root_node
		self._render_visual_graph(node)
  
		# Create the "Output" folder if it doesn't exist
		output_folder = "out"
		if not os.path.exists(output_folder):
			os.makedirs(output_folder)

		# Save the FSM graph as a file
		output_path = os.path.join(output_folder, output_graph_name)
		self.visual_graph.format = "png"
		self.visual_graph.render(output_path, view=False)
   
	def _render_visual_graph(self, node):
		if node is None: return
  	
		for child in node.children:
			if type(node) is RegularGraphNode or type(node) is ConditionalGraphNode:
				self.visual_graph.edge(f"{node.name} {node.id}", f"{child.name} {child.id}", style="solid")
			else:
				self.visual_graph.edge(f"{node.name} {node.id}", f"{child.name} {child.id}", style="dashed")
			self._render_visual_graph(child)

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



class Translator:
	def __init__(self, source_lua_root_node, render_visual_graph):
		self.source_lua_root_node = source_lua_root_node 
		self.render_visual_graph = render_visual_graph
  
		# Graphs
		self.IR_graph = IRGraph(self) 
		self.execution_graph = IRGraph(self)

		# Unpacking flags
		self.unpack_conditionals = False
		self.unpack_loops = False

		# Main function	
		self.main_function_name = None
		self.function_count = 0
		self.inside_main_function = False

		self.node_count = 0
  
	'''
		Translating is done as follows:
		1. BuildIR:
			- Build the Intermediate Representation (IR) graph tree
  			- 1a. Travsering from the root, find all regular, conditional and loop nodes and add them to the graph linearly 
	 		(without going into the branches or loops)
			- 1b. For each branch set it as root and goto 1a.
		2. Modify Assignments: 
  			- Change local assignments to global assignments
			- TODO: Unroll loops?
		3. Linearize Execution: 
			- Find node (x) with a branch child, add other children of (x) to the end of each execution path of the branch child 
		4. Extract functions:
			- Extract and link functions together
		5. Construct AST:
			- Secrete a new lua AST
	'''
	def translate(self):
		# Stage 1
		# Build the graph tree 
  
		logging.info(f"Building IR graph")
		self.buildIR(self.source_lua_root_node)
		if self.render_visual_graph: 
			self.IR_graph.render_visual_graph("IR_graph")


		logging.info(f"Modifying assignments for IR graph")
		self.modify_assignments()
		if self.render_visual_graph: 
			self.IR_graph.render_visual_graph("Modified_IR_graph")
 
		logging.info(f"Linearizing execution")
		self.linearize_execution()
		if self.render_visual_graph: 
			self.execution_graph.render_visual_graph("Exeuction_graph")
 
		logging.info(f"Extracting and linking functions")
		self.extract_functions()
  
		logging.info(f"Constructing new AST")
		self.construct_ast()


	def buildIR(self, node):
		# First collect regular/async statements, branches and loops (without entering)
		logging.debug("Collecting nodes")	
		self.visit(node)

		# Enter the bodies of if statements and loops
		logging.debug("Expanding nodes")	
		for node in self.IR_graph.preorder(self.IR_graph.root_node):
			if type(node) is BranchGraphNode:
				print(node.children)
				for branch in node.children:
					self.IR_graph.pointer = branch
					if(type(branch) is ConditionalGraphNode):
						self.visit(branch.lua_node.body)
					elif(type(branch) is BranchGraphNode):
						raise NotImplementedError("Nested branches")

	# TODO
	def modify_assignments(self):
		pass

	# Find node (x) with a branch child, add other children of (x) to the end of each execution path of the branch child 
	def linearize_execution(self):
	
		for node in self.IR_graph.preorder(self.IR_graph.root_node):
			collect_children = False

			for child in node.children:	
				if type(child) is BranchGraphNode:
					collect_children = True

			new_children = []
			if collect_children:
				pass	
			
	def extract_functions(self):
		pass

	def construct_ast(self):
		pass


	'''
		---------------------------------------------------------------------------------------------------
		Regular nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Assign(self, node):
		self.IR_graph.add_node(RegularGraphNode(lua_node=node))

	'''
		Because of the execution environment, all local assignements will be converted to global assignments
		TODO: Use factorio global table?
	'''
	def visit_LocalAssign(self, node):
		self.visit_Assign(node)
  
	def visit_SemiColon(self, node):
		self.IR_graph.add_node(RegularGraphNode(lua_node=node))

	def visit_Return(self, node):
		raise NotImplementedError()
	
	'''
		---------------------------------------------------------------------------------------------------
		Loop nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Do(self, node):
		raise NotImplementedError()
 
	def visit_While(self, node):
		raise NotImplementedError()

	def visit_Forin(self, node):
		raise NotImplementedError()

	def visit_Fornum(self, node):
		raise NotImplementedError()

	def visit_Repeat(self, node):
		raise NotImplementedError()
	
	def visit_Break(self, node):
		raise NotImplementedError()
 
	'''
		---------------------------------------------------------------------------------------------------
		Conditional nodes
		---------------------------------------------------------------------------------------------------
 	'''
	# def visit_ElseIf(self, node):
	# 	logging.debug(f"Visited ElseIf")
	# 	self.IR_graph.add_node(ConditionalGraphNode(lua_node=node))
  
		# self.visit(node.body)
		# self.visit(node.orelse)

	def visit_If(self, node):
		logging.debug(f"Visited If")
		
		branch_nodes = [ConditionalGraphNode(lua_node=node)]

		else_statement_present = False
  
		lookahead_node = node.orelse
		while(type(lookahead_node) == luaparser.astnodes.ElseIf):
			logging.debug(f"Found ElseIf")
			branch_nodes.append(ConditionalGraphNode(lua_node=lookahead_node))
			lookahead_node = lookahead_node.orelse
		if(lookahead_node is not None):
			logging.debug(f"Found Else")
			branch_nodes.append(ConditionalGraphNode(lua_node=lookahead_node, name="Else"))
  
		previous_pointer = self.IR_graph.pointer
		
		branch_graph_node = BranchGraphNode(else_statement_present)
		self.IR_graph.add_node(branch_graph_node)
  
  
		for branch in branch_nodes:
			self.IR_graph.pointer = branch_graph_node
			self.IR_graph.add_node(branch)
   
		self.IR_graph.pointer = previous_pointer
  
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
  
		self.IR_graph.add_node(RegularGraphNode(lua_node=node))

		self.visit(node.body)

	def visit_LocalFunction(self, node):
		# TODO: Just change function to not be local
		raise Exception("Error: Function must not be a local function")


	def visit_Call(self, node):
		logging.debug(f"Visited {node.func.id} with arguments {node.args}")
		# Find await() calls
		if node.func.id == 'await':
			logging.info(f"Await call found. Function: {node.args[0].func.id}")
			self.IR_graph.add_node(AsyncGraphNode(lua_node=node))
		else:
			# Regular function call
			self.IR_graph.add_node(RegularGraphNode(lua_node=node))

	'''
		---------------------------------------------------------------------------------------------------
		Unsupported nodes	
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Label(self, node):
		raise Exception("Error: Labels are not supported.")

	def visit_Goto(self, node):
		raise Exception("Error: Goto is not supported.")

	def visit_Invoke(self, node):
		raise Exception("Error: Invoking object methods is not supported.")

	def visit_Method(self, node):
		raise Exception("Error: Defining object methods is not supported.")

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


# Given Lua source code
source_code_1 = """
function doThing()
		bar()
		await(foo())
		bar()
end
"""

source_code_2 = """
function doThing()
		local value = bar()
		if value == 1 then
  			await(foo())
		else
			bar()
		end
		bar()
end
"""

source_code_3 = """
function doThing()
	local var = bar()
	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
		end
		bar()
	else
		car()
	end
	bar()
 	if var == thing1 then
		await(foo()) 
	end
	car()
end
"""


source_code_4 = """
function doThing()
	local var = bar()
	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
		end
		bar()
	else
		car()
	end
	bar() 
 	if var == thing1 then
		await(foo())
	elseif var == thing2 then
		bar()
	elseif var == thing3 then
		if var == thing4 then
			car()
		else
			await(far())
		end
		bar()
	else
		car()
	end
	bar()
 
end
"""

# Convert the source code to an AST
source_lua_root_node = ast.parse(source_code_3)

#print(ast.to_pretty_str(tree))
# Create FSM graph

# Translate
translator = Translator(source_lua_root_node, render_visual_graph=True)
translator.translate()



