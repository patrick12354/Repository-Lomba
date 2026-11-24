from pathlib import Path
import nbformat


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v6_discounted_reachability_source.ipynb"
nb = nbformat.read(SOURCE, as_version=4)
setup = nb.cells[2].source
marker = "import seaborn as sns\n"
inline = "import seaborn as sns\n\n# Embed every EDA figure inside the executed notebook.\nget_ipython().run_line_magic('matplotlib', 'inline')\nfrom matplotlib_inline.backend_inline import set_matplotlib_formats\nset_matplotlib_formats('png')\n"
if "set_matplotlib_formats('png')" not in setup:
    assert marker in setup
    setup = setup.replace(marker, inline)
nb.cells[2].source = setup.replace("—", "-").replace("–", "-")
for cell in nb.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None
nbformat.write(nb, SOURCE)
print(SOURCE)
