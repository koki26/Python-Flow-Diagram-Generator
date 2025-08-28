# Code Diagram Creator

## 📖 Introduction

**Code Diagram Creator** is a Python-based tool that analyzes Python source code and generates an **interactive dependency and class diagram**. It parses classes, methods, functions, inheritance relationships, and function calls to help developers understand code structure visually.

The tool provides a **GUI interface** (built with `tkinter`) where you can select a folder containing Python files, scan for classes, and generate an **interactive HTML diagram** powered by **PyVis**.

---

## 📑 Table of Contents

* [Features](#-features)
* [Installation](#-installation)
* [Usage](#-usage)
* [Configuration](#-configuration)
* [Examples](#-examples)
* [Troubleshooting](#-troubleshooting)
* [Dependencies](#-dependencies)
* [Contributors](#-contributors)
* [License](#-license)

---

## ✨ Features

* 🔍 **AST-based analysis** of Python code (detects classes, methods, and functions).
* 📊 **Inheritance visualization** (parent-child class relationships).
* 🔗 **Function call graph** (who calls what).
* 🗂️ **Module clustering** with color-coded nodes.
* 🎨 **Interactive diagrams** with zoom, pan, and hover tooltips.
* 🖥️ **Simple GUI** for selecting folders and filtering classes.
* 📂 **Exports to HTML** so diagrams can be opened in any browser.

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/code-diagram-creator.git
cd code-diagram-creator
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Or manually install:

```bash
pip install pyvis
```

(`tkinter` is included in most Python distributions, but on Linux you may need to install `python3-tk`.)

---

## 🚀 Usage

### Run the application:

```bash
python code_diagram_creator.py
```

### Steps in GUI:

1. **Browse** → Select a folder containing `.py` files.
2. **Scan for Classes** → Lists all detected classes.
3. **Select specific classes** → Focus the diagram only on them.
4. **Generate Diagram** → Creates `code_diagram.html` and opens it in your browser.

---

## 🔧 Configuration

* **Selected Classes**: Leave empty to include all classes and functions.
* **Diagram Colors**: Modules are assigned distinct colors automatically.
* **Output File**: Default is `code_diagram.html`. You can change this in `visualize_interactive()`.

---

## 📂 Examples

Example: Generating a diagram for a Django project.

1. Select project root folder.
2. Scan for classes (models, views, forms, etc.).
3. Generate diagram.

Result:

* Blue arrows → inheritance between classes.
* Red arrows → function/method calls.
* Grey arrows → class-to-method relationships.

---

## 🛠️ Troubleshooting

* **Tkinter not found** → Install with `sudo apt-get install python3-tk` (Linux) or ensure Python includes `tkinter`.
* **Diagram not opening** → Check if `code_diagram.html` exists in the working directory. Open it manually in a browser.
* **Parsing errors** → Some Python files with syntax errors may be skipped.

---

## 📦 Dependencies

* [Python 3.8+](https://www.python.org/)
* [pyvis](https://pyvis.readthedocs.io/)
* [tkinter](https://docs.python.org/3/library/tkinter.html) (GUI framework)

---

## 👨‍💻 Contributors

* **Your Name** – Creator & Maintainer

Contributions welcome! Feel free to open issues or pull requests.

---