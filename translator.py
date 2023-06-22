import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

from lua_parser import parse
from graphviz import Digraph

class FSMTranslator:
    def __init__(self):
        self.graph = Digraph()
        self.current_function = None
    
    def translate(self, tree):
        self.visit(tree)
        return self.graph
    
    def visit(self, node):
        method_name = f"visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)
    
    def generic_visit(self, node):
        for child in node.children():
            self.visit(child)
    
    def visit_Function(self, node):
        function_name = self.visit(node.name)
        self.graph.node(function_name)
        if self.current_function:
            self.graph.edge(self.current_function, function_name)
        self.current_function = function_name
        self.generic_visit(node)
        self.current_function = None
    
    def visit_Call(self, node):
        function_name = self.visit(node.func)
        self.graph.node(function_name)
        if self.current_function:
            self.graph.edge(self.current_function, function_name)
        self.generic_visit(node)
    
    def visit_Name(self, node):
        return node.id

# Example usage:
code = """
function doThing()
    bar()
    foo()
    bar()
end
"""

tree = parse(code)
translator = FSMTranslator()
graph = translator.translate(tree)

# Create the "Output" folder if it doesn't exist
output_folder = "Output"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Save the FSM graph as a file
output_path = os.path.join(output_folder, "fsm_graph")
graph.format = "png"
graph.render(output_path, view=True)
