
from utils.random_util import RandomUtil
from utils.graph_util import *

from IR_nodes import *

import copy


random_util = RandomUtil(123)

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
		new_instance = cls.__new__(cls)
		for attr, value in self.__dict__.items():
			if isinstance(value, list):
				setattr(new_instance, attr, copy.deepcopy(value))
			else:
				setattr(new_instance, attr, value)

		new_instance.IR_graph = None
		new_instance.id = -1
		new_instance.lua_node = self.lua_node
		new_instance.name = self.name
		new_instance.parent = None
		new_instance.children = []
		return new_instance

	# def __copy__(self):
	# 	cls = self.__class__
	# 	result = cls.__new__(cls)
	# 	result.IR_graph = None
	# 	result.id = -1
	# 	result.lua_node = self.lua_node
	# 	result.name = self.name
	# 	result.parent = None
	# 	result.children = []
	# 	return result

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
	def __init__(self, linked_graph, async_link):
		super().__init__(lua_node=None)
		self.async_link = async_link
		self.generated_link_name = random_util.generate_function_name()
		self.name = "Link " + ("(A) " if self.async_link else "") + self.generated_link_name[5:10] + " → " + linked_graph.generated_name[5:10] + " (G)" 
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
	Placeholder for setting the event pointer
'''
class GeneratedSetEventPointerNode(GeneratedIRGraphNode):
	def __init__(self, pointer):
		super().__init__(lua_node=None)
		self.name = "SetEventPointer " + pointer[5:10]
		self.pointer = pointer
  

