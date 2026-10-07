"""Execute actual notebook cells as ordinary Python and capture their stdout."""

import contextlib
import io
import platform
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / "notebooks/01_accounting.ipynb"
notebook = nbformat.read(path, as_version=4)
namespace = {"__name__": "__main__"}
count = 0
for cell in notebook.cells:
    if cell.cell_type != "code":
        continue
    count += 1
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        exec(compile(cell.source, str(path) + "#" + cell.id, "exec"), namespace)
    cell.execution_count = count
    cell.outputs = [nbformat.v4.new_output("stream", name="stdout", text=output.getvalue())]
notebook.metadata["execution_mode"] = (
    "sequential ordinary Python with actual stdout; no Jupyter kernel"
)
notebook.metadata["language_info"] = {"name": "python", "version": platform.python_version()}
nbformat.validate(notebook)
nbformat.write(notebook, path)
print(f"Executed {count} actual Python cells; mode and environment explicitly recorded.")
