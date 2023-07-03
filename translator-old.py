import os

import luaparser.ast as ast
from luaparser.astnodes import *
from luaparser.astnodes import Node

from graphviz import Digraph

from typing import List
import string
import random
import logging


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
		self.children.append(children)
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

class ConditionalGraphNode(GraphNode):
	def __init__(self, lua_node, id):
		super().__init__(lua_node, id)

class LoopGraphNode(GraphNode):
	def __init__(self, lua_node, id):
		super().__init__(lua_node, id)



class FSMGraph:
	def __init__(self, fsm_translator):
		self.fsm_translator = fsm_translator
		self.visual_graph = Digraph()
  
		self.root_node = None
		self.last_added_node = None
		self.pointer = None
  
  
		

	def add_node(self, graph_node):
     
		# Initialize root node to main function definition
		if self.root_node == None and self.fsm_translator.inside_main_function:
			self.root_node = graph_node
			self.pointer = self.root_node
			return
   

		self.visual_graph.edge(f"{self.pointer.name} {self.pointer.id}", f"{graph_node.name} {graph_node.id}")
  
		if(type(graph_node) is RegularGraphNode):
			self.pointer.add_children([graph_node])
		elif(type(graph_node) is AsyncGraphNode):
			self.pointer.add_children([graph_node])
		elif(type(graph_node) is ConditionalGraphNode):
			raise NotImplementedError()
		elif(type(graph_node) is LoopGraphNode):
			raise NotImplementedError()

		self.pointer = graph_node



 
	def get_next_node(self):
		if self.pointer and self.pointer.children:
			return self.pointer.children[0]
		return None

	def move_pointer_to_next_node(self):
		# Move the pointer to the next node
		if self.pointer and self.pointer.children:
			self.pointer = self.pointer.children[0]




class FSMTranslator:
	def __init__(self):
		self.fsm_graph = FSMGraph(self) 

		# Main function	
		self.main_function_name = None
		self.function_count = 0
		self.inside_main_function = False

		self.node_stacks = []
		self.curr_node_stack = []

		self.node_count = 0
  
	def generate_event_name(self):
		return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


	'''
		---------------------------------------------------------------------------------------------------
		Regular nodes
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Assign(self, node):
		raise NotImplementedError()

	def visit_LocalAssign(self, node):
		raise NotImplementedError()

	def visit_SemiColon(self, node):
		raise NotImplementedError()

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
	def visit_ElseIf(self, node):
		raise NotImplementedError()

	def visit_If(self, node):
		raise NotImplementedError()

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
  
		self.fsm_graph.add_node(RegularGraphNode(node, self.node_count))
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
			# Append node stack and reset it
			self.node_stacks.append(self.curr_node_stack)
			self.curr_node_stack = []
		else:
			# Regular function call
			self.fsm_graph.add_node(RegularGraphNode(node, self.node_count))
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
		if self.inside_main_function:
			self.curr_node_stack.append(node)
		method = 'visit_' + node.__class__.__name__
		#get correct visit function
		visitor = getattr(self, method, self.generic_visit)
		#call visit function with current node
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
source_code = """
function doThing()
		bar()
		await(foo())
		bar()
end
"""

# Convert the source code to an AST
tree = ast.parse(source_code)

#print(ast.to_pretty_str(tree))
# Create FSM graph

# Walk the AST
translator = FSMTranslator()
translator.visit(tree)

# Create the "Output" folder if it doesn't exist
output_folder = "out"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Save the FSM graph as a file
output_path = os.path.join(output_folder, "fsm_graph")
translator.fsm_graph.visual_graph.format = "png"
translator.fsm_graph.visual_graph.render(output_path, view=False)
