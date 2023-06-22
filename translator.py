import luaparser.ast as ast
from graphviz import Digraph

class FSMTranslator(ast.ASTVisitor):
    def __init__(self):
        self.graph = Digraph()
    
    def translate(self, tree):
        self.visit(tree)
        return self.graph
    
    def visit_Chunk(self, node):
        self.visit(node.body)
    
    def visit_Block(self, node):
        for stmt in node.body:
            self.visit(stmt)
    
    def visit_Assign(self, node):
        variable_name = node.targets[0].id
        self.graph.node(variable_name)
        self.visit(node.value)
    
    def visit_BinaryOp(self, node):
        operation = str(node.op)
        self.graph.node(operation)
        
        self.visit(node.left)
        self.visit(node.right)
        
        self.graph.edge(operation, str(node.left))
        self.graph.edge(operation, str(node.right))
        
# Example usage:
code = """
-- Sample Lua code
local x = 10
local y = x + 5
"""

tree = ast.parse(code)
translator = FSMTranslator()
graph = translator.translate(tree)

# Output the FSM graph (requires 'graphviz' package)
graph.render("fsm_graph", format="png", view=True)
