import luaparser.ast as ast
from luaparser.astnodes import *
from typing import List
import string
import random

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
	def __init__(self, lua_node):
		self.lua_node = lua_node
		self.parent = None
		self.children = None
  

class RegularGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

class AsyncGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)

class LoopGraphNode(GraphNode):
	def __init__(self, lua_node):
		super().__init__(lua_node)



class FSMGraph:
	def __init__(self):
		self.root_node = None
		self.pointer = None
		

	def add_node(self, graph_node):
		# Initialize
		if self.root_node == None:
			self.root_node = graph_node
			self.pointer = self.root_node




class EventFSMVisitor:
	def __init__(self, fsm_graph):
		self.fsm_graph = fsm_graph 

		# Main function	
		self.main_function_name = None
		self.function_count = 0
		self.inside_main_function = False

		self.node_stacks = []
		self.curr_node_stack = []


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
		if self.function_count > 0:
			raise Exception("Error: More than one function defined. Scripts should only contain one function definition.")
		
		self.function_count += 1
		self.main_function_name = node.name

		# We are now traversing inside the main function
		self.inside_main_function = True

		self.visit(node.body)

	def visit_LocalFunction(self, node):
		# TODO: Just change function to not be local
		raise Exception("Error: Function must not be a local function")


	def visit_Call(self, node):
		# Find await() calls
		if node.func.id == 'await':
			# Append node stack and reset it
			self.node_stacks.append(self.curr_node_stack)
			self.curr_node_stack = []

	'''
		---------------------------------------------------------------------------------------------------
		Unsupported nodes	
		---------------------------------------------------------------------------------------------------
 	'''
	def visit_Label(self, node):
		raise Exception("Error: Labels are not supported.")

	def visit_Goto(self, node):
		raise Exception("Error: Goto is not supported.")

	'''
		---------------------------------------------------------------------------------------------------
		Call sorting
		---------------------------------------------------------------------------------------------------
 	'''
	def visit(self, node):
		if self.inside_main_function:
			self.curr_node_stack.append(node)
		method = 'visit_' + node.__class__.__name__
		visitor = getattr(self, method, self.generic_visit)
		return visitor(node)

	def generic_visit(self, node):
		if isinstance(node, list):
			for item in node:
				self.visit(item)
		elif isinstance(node, Node):
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
		finish(foo())
		bar()
end
"""

# Convert the source code to an AST
tree = ast.parse(source_code)

# Create FSM graph
fsm_graph = FSMGraph()

# Walk the AST
visitor = EventFSMVisitor(fsm_graph)
visitor.visit(tree)



# next_event_name = self.generate_event_name()
# next_event_func_name = next_event_name + "_event_func"

# # Store the next event in the pointers
# print(f"global.event_ptrs['{func_name}'] = {next_event_func_name}")
# print(f"global.event_names['{next_event_func_name}'] = generate_event_name()")
# print(f"script.on_event(global.events['{next_event_func_name}'], function () {next_event_func_name}() end)")

# # Generate the next event function
# print(f"function {next_event_func_name}()")
# for arg in node.args:
# # if isinstance(arg, FuncCall):
# print(f"    {arg.func.id}()")
# print("end")