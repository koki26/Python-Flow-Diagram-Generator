import ast
from pyvis.network import Network

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = {}
        self.standalone_funcs = []
        self.inheritance = {}
        self.edges = []
        self.func_info = {}

    def visit_ClassDef(self, node):
        class_name = node.name
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.inheritance[class_name] = bases[0] if bases else None
        self.classes[class_name] = []

        for n in node.body:
            if isinstance(n, ast.FunctionDef):
                method_name = f"{class_name}.{n.name}"
                self.classes[class_name].append(method_name)
                self.func_info[method_name] = self.get_func_info(n)
                self.visit_FunctionDef(n, parent=method_name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node, parent=None):
        if parent is None:
            self.standalone_funcs.append(node.name)
            self.func_info[node.name] = self.get_func_info(node)

        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Attribute):
                    callee = f"{n.func.value.id}.{n.func.attr}" if isinstance(n.func.value, ast.Name) else n.func.attr
                elif isinstance(n.func, ast.Name):
                    callee = n.func.id
                else:
                    continue
                if parent:
                    self.edges.append((parent, callee))
                else:
                    self.edges.append((node.name, callee))

    @staticmethod
    def get_func_info(node):
        args = [a.arg for a in node.args.args]
        signature = f"({', '.join(args)})"
        doc = ast.get_docstring(node)
        doc = doc if doc else "No docstring"
        return f"{node.name}{signature}\n{doc}"

def parse_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    analyzer = CodeAnalyzer()
    analyzer.visit(tree)
    return analyzer.classes, analyzer.standalone_funcs, analyzer.inheritance, analyzer.edges, analyzer.func_info

def visualize_interactive(classes, standalone_funcs, inheritance, edges, func_info, output_file="code_diagram.html"):
    net = Network(height="900px", width="100%", directed=True, notebook=False, bgcolor="#f0f0f0")
    net.barnes_hut(gravity=-80000, central_gravity=0.3)

    # Add cluster nodes for classes
    for cls, methods in classes.items():
        cluster_id = f"cluster_{cls}"
        net.add_node(cluster_id, label=cls, color="#89CFF0", shape="box", font={"size": 36, "face": "Arial"}, physics=False)
        for m in methods:
            net.add_node(
                m,
                label=m,
                title=func_info.get(m, "No info"),
                color="#a0c4ff",
                shape="box",
                font={"size": 30, "face": "Arial", "multi": True}
            )
            net.add_edge(cluster_id, m, color="#89CFF0", width=2, smooth=True)

    # Add standalone functions
    for func in standalone_funcs:
        net.add_node(
            func,
            label=func,
            title=func_info.get(func, "No info"),
            color="#b9fbc0",
            shape="ellipse",
            font={"size": 30, "face": "Arial", "multi": True}
        )

    # Inheritance edges (gray, dashed)
    for cls, parent in inheritance.items():
        if parent:
            net.add_node(f"cluster_{parent}", label=parent, color="#89CFF0", shape="box")
            net.add_edge(f"cluster_{parent}", f"cluster_{cls}", color="gray", title="Inheritance", width=3, arrows="to", smooth=True)

    # Function call edges (black) with safe node creation
    for src, dst in edges:
        try:
            net.get_node(src)
        except KeyError:
            net.add_node(src, label=src, color="#ffb347", shape="ellipse", font={"size": 24, "face": "Arial"})
        try:
            net.get_node(dst)
        except KeyError:
            net.add_node(dst, label=dst, color="#ffb347", shape="ellipse", font={"size": 24, "face": "Arial"})
        net.add_edge(src, dst, color="black", title="Function call", width=2, smooth=True)

    # Show the network
    net.show(output_file, notebook=False)
    print(f"Interactive diagram saved as {output_file}")

if __name__ == "__main__":
    filename = input("Enter Python file path: ")
    classes, standalone_funcs, inheritance, edges, func_info = parse_file(filename)
    visualize_interactive(classes, standalone_funcs, inheritance, edges, func_info)
