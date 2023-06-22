import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files/Graphviz/bin/'

import luaparser.ast as ast
from graphviz import Digraph

class FSMTranslator(ast.ASTVisitor):
    def __init__(self):
        self.graph = Digraph()
    
    def translate(self, tree):
        self.visit(tree)
        return self.graph
    
    def visit_FunctionDef(self, node):
        self.visit(node.body)
    
    def visit_Call(self, node):
        function_name = node.func.id
        self.graph.node(function_name)
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
            self.graph.edge(function_name, str(arg))
    
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

tree = ast.parse(code)
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
