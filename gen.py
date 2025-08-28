import ast
import json
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pyvis.network import Network

class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, module_name):
        self.module_name = module_name
        self.classes = {}
        self.standalone_funcs = []
        self.inheritance = {}
        self.edges = []
        self.func_info = {}
        self.modules = {}

    def visit_ClassDef(self, node):
        class_name = f"{self.module_name}.{node.name}"
        self.modules[class_name] = self.module_name
        bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
        self.inheritance[class_name] = f"{self.module_name}.{bases[0]}" if bases else None
        self.classes[class_name] = []

        for n in node.body:
            if isinstance(n, ast.FunctionDef):
                method_name = f"{class_name}.{n.name}"
                self.classes[class_name].append(method_name)
                self.func_info[method_name] = self.get_func_info(n)
                self.visit_FunctionDef(n, parent=method_name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node, parent=None):
        name = f"{self.module_name}.{node.name}" if parent is None else parent
        if parent is None:
            self.standalone_funcs.append(name)
            self.func_info[name] = self.get_func_info(node)

        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Attribute):
                    if isinstance(n.func.value, ast.Name):
                        callee = f"{n.func.value.id}.{n.func.attr}"
                    elif isinstance(n.func.value, ast.Attribute):
                        # Handle chained attributes like obj.attr.method
                        callee = self.get_full_attribute_name(n.func.value) + f".{n.func.attr}"
                    else:
                        callee = n.func.attr
                elif isinstance(n.func, ast.Name):
                    callee = n.func.id
                else:
                    continue
                
                if parent:
                    self.edges.append((parent, callee))
                else:
                    self.edges.append((name, callee))

    def get_full_attribute_name(self, node):
        """Recursively get the full name of an attribute chain"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self.get_full_attribute_name(node.value)}.{node.attr}"
        return "unknown"

    @staticmethod
    def get_func_info(node):
        args = [a.arg for a in node.args.args]
        signature = f"({', '.join(args)})"
        doc = ast.get_docstring(node) or "No docstring"
        return f"{node.name}{signature}\n{doc}"

def parse_folder(folder, selected_classes=None):
    all_classes, all_funcs, all_inheritance, all_edges, all_func_info, all_modules = {}, [], {}, [], {}, {}
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                module_name = os.path.splitext(os.path.relpath(path, folder))[0].replace(os.sep, ".")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())
                    analyzer = CodeAnalyzer(module_name)
                    analyzer.visit(tree)
                    
                    # Filter classes if specific classes are selected
                    if selected_classes:
                        filtered_classes = {}
                        filtered_inheritance = {}
                        filtered_modules = {}
                        filtered_func_info = {}
                        filtered_edges = []
                        
                        for cls_name, methods in analyzer.classes.items():
                            short_name = cls_name.split('.')[-1]
                            if short_name in selected_classes:
                                filtered_classes[cls_name] = methods
                                filtered_modules[cls_name] = analyzer.modules.get(cls_name, 'main')
                                if cls_name in analyzer.inheritance:
                                    filtered_inheritance[cls_name] = analyzer.inheritance[cls_name]
                                
                                # Add method info
                                for method in methods:
                                    if method in analyzer.func_info:
                                        filtered_func_info[method] = analyzer.func_info[method]
                        
                        # Filter edges that involve selected classes
                        for src, dst in analyzer.edges:
                            # Check if source or destination is in selected classes
                            src_in_selected = any(cls in src for cls in selected_classes)
                            dst_in_selected = any(cls in dst for cls in selected_classes)
                            
                            if src_in_selected or dst_in_selected:
                                filtered_edges.append((src, dst))
                        
                        all_classes.update(filtered_classes)
                        all_inheritance.update(filtered_inheritance)
                        all_modules.update(filtered_modules)
                        all_func_info.update(filtered_func_info)
                        all_edges.extend(filtered_edges)
                        all_funcs.extend([f for f in analyzer.standalone_funcs if any(cls in f for cls in selected_classes)])
                    else:
                        # Include everything if no classes are selected
                        all_classes.update(analyzer.classes)
                        all_funcs.extend(analyzer.standalone_funcs)
                        all_inheritance.update(analyzer.inheritance)
                        all_edges.extend(analyzer.edges)
                        all_func_info.update(analyzer.func_info)
                        all_modules.update(analyzer.modules)
                except Exception as e:
                    print(f"Failed to parse {path}: {e}")
    return all_classes, all_funcs, all_inheritance, all_edges, all_func_info, all_modules

def visualize_interactive(classes, standalone_funcs, inheritance, edges, func_info, modules, output_file="code_diagram.html"):
    net = Network(height="900px", width="100%", directed=True, notebook=False, bgcolor="#f0f0f0")
    net.barnes_hut(gravity=-80000, central_gravity=0.3, spring_length=200)

    cluster_children = {}
    module_colors = ["#89CFF0", "#a0c4ff", "#b9fbc0", "#ffb347", "#ff6961", "#caffbf", "#ffd6a5"]
    module_color_map = {}
    all_module_names = list(set(modules.values()))
    for i, mod in enumerate(all_module_names):
        module_color_map[mod] = module_colors[i % len(module_colors)]

    # Add class clusters
    for cls, methods in classes.items():
        module = modules.get(cls, 'main')
        cluster_id = f"cluster_{cls}"
        net.add_node(cluster_id, label=cls, color=module_color_map[module], shape="box",
                     font={"size":36, "face":"Arial"}, physics=True)
        cluster_children[cluster_id] = methods
        for m in methods:
            net.add_node(m, label=m, title=func_info.get(m, "No info"),
                         color=module_color_map[module], shape="box",
                         font={"size":30, "face":"Arial", "multi":True}, physics=True)

    # Standalone functions
    for func in standalone_funcs:
        net.add_node(func, label=func, title=func_info.get(func, "No info"),
                     color="#b9fbc0", shape="ellipse",
                     font={"size":30, "face":"Arial", "multi":True}, physics=True)

    # Add edges from classes to their methods
    for cls, methods in classes.items():
        cluster_id = f"cluster_{cls}"
        for m in methods:
            net.add_edge(cluster_id, m, color="#888888", width=1, smooth=True)

    # Inheritance edges
    for cls, parent in inheritance.items():
        if parent:
            # Check if both classes exist in our visualization
            parent_exists = any(node['id'] == f"cluster_{parent}" for node in net.nodes)
            cls_exists = any(node['id'] == f"cluster_{cls}" for node in net.nodes)
            
            if parent_exists and cls_exists:
                net.add_edge(f"cluster_{parent}", f"cluster_{cls}", color="blue", title="Inheritance", width=3, arrows="to", smooth=True)

    # Function call edges
    for src, dst in edges:
        # Check if both source and destination exist in our nodes
        src_exists = any(node['id'] == src for node in net.nodes)
        dst_exists = any(node['id'] == dst for node in net.nodes)
        
        if src_exists and dst_exists:
            net.add_edge(src, dst, color="red", title="Function call", width=2, smooth=True)

    net.show(output_file, notebook=False)

    # Inject JS
    with open(output_file, "r", encoding="utf-8") as f:
        html = f.read()

    js_snippet = f"""
<script>
// Loading overlay
var overlay = document.createElement('div');
overlay.id = 'loadingOverlay';
overlay.style.position = 'fixed';
overlay.style.top = '0';
overlay.style.left = '0';
overlay.style.width = '100%';
overlay.style.height = '100%';
overlay.style.backgroundColor = 'rgba(255,255,255,0.8)';
overlay.style.zIndex = '9999';
overlay.style.display = 'flex';
overlay.style.justifyContent = 'center';
overlay.style.alignItems = 'center';
overlay.style.fontSize = '24px';
overlay.innerHTML = 'Loading network...';
document.body.appendChild(overlay);

// Hide overlay after first full draw
network.once('afterDrawing', function() {{
    setTimeout(function() {{
        overlay.style.display = 'none';
        network.fit({{animation: true}});
        
        // Add instructions
        var instructions = document.createElement('div');
        instructions.style.position = 'absolute';
        instructions.style.top = '10px';
        instructions.style.right = '10px';
        instructions.style.backgroundColor = 'rgba(255, 255, 255, 0.8)';
        instructions.style.padding = '10px';
        instructions.style.borderRadius = '5px';
        instructions.style.fontSize = '14px';
        instructions.style.zIndex = '1000';
        instructions.innerHTML = '<strong>Legend:</strong><br>' +
                                 '<span style="color:blue">Blue</span>: Inheritance<br>' +
                                 '<span style="color:red">Red</span>: Function calls<br>' +
                                 '<span style="color:#888">Gray</span>: Class methods';
        document.body.appendChild(instructions);
    }}, 100);
}});
</script>
<style>
    body {{
        margin: 0;
        padding: 0;
        font-family: Arial, sans-serif;
        overflow: hidden;
    }}
    
    #mynetwork {{
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
    }}
</style>
"""

    html = html.replace("</body>", js_snippet + "</body>")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Interactive diagram ready: {output_file}")

class DiagramCreator:
    def __init__(self, root):
        self.root = root
        self.root.title("Code Diagram Creator")
        self.root.geometry("500x400")
        self.root.configure(bg="#f5f5f5")
        
        self.folder_path = tk.StringVar()
        self.selected_classes = []
        self.all_classes = []
        
        self.create_widgets()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Code Diagram Creator", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Folder selection
        folder_frame = ttk.Frame(main_frame)
        folder_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        ttk.Label(folder_frame, text="Select Folder:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_path, width=40)
        folder_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(folder_frame, text="Browse", command=self.browse_folder)
        browse_btn.grid(row=1, column=1)
        
        # Scan button
        scan_btn = ttk.Button(main_frame, text="Scan for Classes", command=self.scan_classes)
        scan_btn.grid(row=2, column=0, columnspan=2, pady=(0, 20))
        
        # Classes selection
        ttk.Label(main_frame, text="Select Classes to Include (leave empty for all):").grid(row=3, column=0, sticky=tk.W, pady=(0, 5))
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(main_frame)
        list_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        self.classes_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=10)
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.classes_listbox.yview)
        self.classes_listbox.configure(yscrollcommand=scrollbar.set)
        
        self.classes_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Select all/none buttons
        select_buttons_frame = ttk.Frame(main_frame)
        select_buttons_frame.grid(row=5, column=0, columnspan=2, pady=(0, 20))
        
        ttk.Button(select_buttons_frame, text="Select All", command=self.select_all).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(select_buttons_frame, text="Select None", command=self.select_none).grid(row=0, column=1)
        
        # Generate button
        generate_btn = ttk.Button(main_frame, text="Generate Diagram", command=self.generate_diagram)
        generate_btn.grid(row=6, column=0, columnspan=2, pady=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(main_frame, text="", foreground="green")
        self.status_label.grid(row=7, column=0, columnspan=2)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="Select Folder Containing Python Files")
        if folder:
            self.folder_path.set(folder)
    
    def scan_classes(self):
        folder = self.folder_path.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return
        
        self.all_classes = []
        self.classes_listbox.delete(0, tk.END)
        
        try:
            # Quick scan to find all classes
            for root, _, files in os.walk(folder):
                for file in files:
                    if file.endswith(".py"):
                        path = os.path.join(root, file)
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                tree = ast.parse(f.read())
                            
                            for node in ast.walk(tree):
                                if isinstance(node, ast.ClassDef):
                                    self.all_classes.append(node.name)
                        except:
                            continue
            
            # Add classes to listbox
            for cls in sorted(set(self.all_classes)):
                self.classes_listbox.insert(tk.END, cls)
            
            self.status_label.config(text=f"Found {len(set(self.all_classes))} unique classes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan folder: {e}")
    
    def select_all(self):
        self.classes_listbox.select_set(0, tk.END)
    
    def select_none(self):
        self.classes_listbox.select_clear(0, tk.END)
    
    def generate_diagram(self):
        folder = self.folder_path.get()
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "Please select a valid folder")
            return
        
        # Get selected classes
        selected_indices = self.classes_listbox.curselection()
        selected_classes = [self.classes_listbox.get(i) for i in selected_indices] if selected_indices else None
        
        self.status_label.config(text="Generating diagram...")
        self.root.update()
        
        try:
            classes, standalone_funcs, inheritance, edges, func_info, modules = parse_folder(folder, selected_classes)
            visualize_interactive(classes, standalone_funcs, inheritance, edges, func_info, modules)
            self.status_label.config(text="Diagram generated successfully!")
            
            # Open the diagram in the default browser
            import webbrowser
            webbrowser.open("code_diagram.html")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate diagram: {e}")
            self.status_label.config(text="")

if __name__ == "__main__":
    root = tk.Tk()
    app = DiagramCreator(root)
    root.mainloop()