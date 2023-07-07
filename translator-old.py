import os

import luaparser
import luaparser.ast as ast
from luaparser.astnodes import *
from luaparser.astnodes import Node

from graphviz import Digraph

from typing import List
import string
import random
import logging
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

logging.basicConfig(level=logging.DEBUG, format='%(funcName)s :: %(levelname)s :: %(message)s')

'''
	Converts lua code to an event-driven finite state machine (substitute for coroutines)
	- Splits functions into multiple functions, seperated by async events
	- Async events defined by await(foo()) calls
	- Handles events inside conditional blocks

	Limitations:
	- Gotos and labels are not supported
	- Objects/Methods are not supported
	- Must track global table of async functions
'''


class GraphNode:
	def __init__(self, lua_node, id):
		self.id = id
		self.lua_node = lua_node
		self.name = lua_node._name
		self.parent = None
		self.children = []
  
	def add_children(self, children):
		self.children.extend(children)
		for child in children:
			child.parent = self	
  
  
'''
	Regular graph nodes are any sort of exeuction that does not introduce differing levels of heirarchy or asynchronous calls
'''
class RegularGraphNode(GraphNode):
	def __init__(self, lua_node, id):
		super().__init__(lua_node, id)

'''
	Asynchronous function calls. 
'''
class AsyncGraphNode(GraphNode):
	def __init__(self, lua_node, id):
		super().__init__(lua_node, id)
		self.name = '(async) ' + lua_node._name 


'''
	Intermediate reprsentation for conditionals. This node will contain each elseif/else statement.
'''
class BranchGraphNode(GraphNode):
	def __init__(self, id, branch_nodes):
		self.id = id
		self.name = 'Branch'
		self.children = branch_nodes 
'''
	Conditional graph nodes contain all statements related to an if statement.
'''
class ConditionalGraphNode(GraphNode):
	def __init__(self, lua_node, id, name=""):
		super().__init__(lua_node, id)
		if name != "": self.name = name
	
class LoopGraphNode(GraphNode):
	def __init__(self, lua_node, id):
		super().__init__(lua_node, id)

class FSMGraph:
	def __init__(self, fsm_translator):
		self.fsm_translator = fsm_translator
		self.visual_graph = Digraph()
  
		self.root_node = None
		self.main_pointer = None
  
	def add_node(self, graph_node):
	 
		# Initialize root node to main function definition
		if self.root_node is None and self.fsm_translator.inside_main_function:
			self.root_node = graph_node
			self.pointer = self.root_node
			return
  
		self.pointer.add_children([graph_node])

		if(type(graph_node) is not BranchGraphNode):
			self.pointer = graph_node

	def get_descendants(self, node):
		return self._get_descendants(node, [])
  
	def _get_descendants(self, node, children):
		if not node.children: return []
  	
		for child in node.children:
			children.append(child)
			children.append(self._get_descendants(child))
	 
	def render_visual_graph(self, node=None):
		if node is None: node = self.root_node
		self._render_visual_graph(node)
   
	def _render_visual_graph(self, node):
		if node is None: return
  	
		for child in node.children:
			if type(node) is RegularGraphNode:
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


class FSMTranslator:
	def __init__(self, source_lua_root_node):
		self.source_lua_root_node = source_lua_root_node 
  
		# Graph
		self.fsm_graph = FSMGraph(self) 

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
		1. Travsering from the root, find all regular, conditional and loop nodes and add them to the graph linearly (without going into the branches or loops)
		2. For each branch set it as root and goto 2.
		3. 
	'''
	def translate(self):
		# Collect regular/async statements, conditionals (skipping the innards) and loops
		self.visit(self.source_lua_root_node)
  
		# Visit the bodies of if statements
		# TODO: Nested if statements
		for node in self.fsm_graph.preorder(self.fsm_graph.root_node):
			print(node)
			if(type(node) is BranchGraphNode):
				for branch in node.children:
					# Deal with nested here
					self.fsm_graph.pointer = branch
        
					if(type(branch) is ConditionalGraphNode):
						self.visit(branch.lua_node.body)
					elif(type(branch) is BranchGraphNode):
						print("Nested branches")




	'''
		---------------------------------------------------------------------------------------------------
		Regular nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Assign(self, node):
		self.fsm_graph.add_node(RegularGraphNode(lua_node=node, id=self.node_count))
		self.node_count += 1

	'''
		Because of the execution environment, all local assignements will be converted to global assignments
		TODO: Use factorio global table?
	'''
	def visit_LocalAssign(self, node):
		self.visit_Assign(node)
  
	def visit_SemiColon(self, node):
		self.fsm_graph.add_node(RegularGraphNode(lua_node=node, id=self.node_count))
		self.node_count += 1

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
	# 	self.fsm_graph.add_node(ConditionalGraphNode(lua_node=node, id=self.node_count))
	# 	self.node_count += 1
  
		# self.visit(node.body)
		# self.visit(node.orelse)

	def visit_If(self, node):
		logging.debug(f"Visited If")
		logging.debug(f"Begin lookahead")
		
		branch_nodes = [ConditionalGraphNode(lua_node=node, id=self.node_count)]
		self.node_count += 1
  
		lookahead_node = node.orelse
		while(type(lookahead_node) == luaparser.astnodes.ElseIf):
			branch_nodes.append(ConditionalGraphNode(lua_node=lookahead_node, id=self.node_count))
			self.node_count += 1
			lookahead_node = lookahead_node.orelse

		# Is there a closing else statement
		if(lookahead_node is not None):
			branch_nodes.append(ConditionalGraphNode(lua_node=lookahead_node, id=self.node_count, name="Else"))
			self.node_count += 1
   
		self.fsm_graph.add_node(BranchGraphNode(id=self.node_count, branch_nodes=branch_nodes))
		self.node_count += 1
  
		# self.visit(node.body)
		# self.visit(node.orelse)

	'''
		---------------------------------------------------------------------------------------------------
		Function definition/calling nodes
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
  
		self.fsm_graph.add_node(RegularGraphNode(lua_node=node, id=self.node_count))
		self.node_count += 1

		self.visit(node.body)

	def visit_LocalFunction(self, node):
		# TODO: Just change function to not be local
		raise Exception("Error: Function must not be a local function")


	def visit_Call(self, node):
		logging.debug(f"Visited {node.func.id} with arguments {node.args}")
		# Find await() calls
		if node.func.id == 'await':
			logging.info(f"Await call found. Function: {node.args[0].func.id}")
			self.fsm_graph.add_node(AsyncGraphNode(lua_node=node, id=self.node_count))
			self.node_count += 1
		else:
			# Regular function call
			self.fsm_graph.add_node(RegularGraphNode(lua_node=node, id=self.node_count))
			self.node_count += 1

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
end
"""

# Convert the source code to an AST
source_lua_root_node = ast.parse(source_code_3)

#print(ast.to_pretty_str(tree))
# Create FSM graph

# Translate
translator = FSMTranslator(source_lua_root_node)
translator.translate()

translator.fsm_graph.render_visual_graph()

# Create the "Output" folder if it doesn't exist
output_folder = "out"
if not os.path.exists(output_folder):
	os.makedirs(output_folder)

# Save the FSM graph as a file
output_path = os.path.join(output_folder, "fsm_graph")
translator.fsm_graph.visual_graph.format = "png"
translator.fsm_graph.visual_graph.render(output_path, view=False)
