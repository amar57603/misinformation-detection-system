import json
import os
import sys

print("========================================================")
print("  Extracting and executing Jupyter Notebook pipeline...")
print("========================================================")

notebook_path = os.path.join("notebooks", "data_preprocessing_and_training.ipynb")
if not os.path.exists(notebook_path):
    print(f"Error: Notebook not found at {notebook_path}")
    sys.exit(1)

# Read notebook
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Extract python code from all code cells
code_blocks = []
for cell in nb["cells"]:
    if cell["cell_type"] == "code":
        # Join lines of code
        code_lines = cell["source"]
        code_blocks.append("".join(code_lines))

# Combine code blocks
full_code = "\n\n# --- CELL SPLIT --- \n\n".join(code_blocks)

# Change working directory to notebooks/ so that relative paths like ../data/ resolve correctly
os.chdir("notebooks")

# Add the parent directory to sys.path so scripts folder can be found if needed
sys.path.insert(0, os.path.dirname(os.getcwd()))

try:
    # Execute the code in the global context
    exec(full_code, globals())
except Exception as e:
    print(f"\nExecution error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n========================================================")
print("  Jupyter Notebook Pipeline Completed Successfully!")
print("========================================================")
