import luaparser.ast as ast
from luaparser.astnodes import *
from typing import List
import string
import random

'''
	Converts lua code to an event-driven finite state machine (substitute for coroutines)
	- Splits functions into multiple functions, seperated by async events
	- Async events defined by await(foo()) calls
	- Handles events inside conditional and loop blocks

	Limitations:
	- Loops are not supported
	- Gotos and labels are not supported
	- Must track global table of async functions
'''


class EventFSMTreeGenerator:
	def __init__(self, source_tree):
		self.source_tree = source_tree
		self.visitor = EventFSMVisitor(self)
		
		self.top_level_functions = [] 

	def create_on_event_function(event_id):
		pass

	def generate(self):
		self.visitor.visit()

	def add_node(self):
		pass

	def construct_function():
		pass

	def render():
		pass

class EventFSMVisitor:
	def __init__(self, tree_generator):
		self.tree_generator = tree_generator

		# Main function	
		self.main_function_name: Expression = None
		self.function_count: Number = 0
		self.inside_main_function = False

		self.node_stacks = []
		self.curr_node_stack = []


	def generate_event_name(self):
		return ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))


	'''
		Local functions should not exist, throw an error
	'''
	def visit_LocalFunction(self, node):
		raise Exception("Error: Function must not be a local function")

	'''
		Find and extract the main function name for the script.
		Note: There should be only one main function.
	'''
	def visit_Function(self, node):
		if self.function_count > 0:
			raise Exception("Error: More than one function defined. Scripts should only contain one function definition.")
		
		self.function_count += 1
		self.main_function_name = node.name

		# We are now traversing inside the main function
		self.inside_main_function = True

		self.visit(node.body)

	def visit_Call(self, node):
		# Find await() calls
		if node.func.id == 'await':
			# Append node stack and reset it
			self.node_stacks.append(self.curr_node_stack)
			self.curr_node_stack = []

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

# Construct the new tree generator
tree_generator = EventFSMTreeGenerator()

# Walk the AST
visitor = EventFSMVisitor(tree_generator)
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