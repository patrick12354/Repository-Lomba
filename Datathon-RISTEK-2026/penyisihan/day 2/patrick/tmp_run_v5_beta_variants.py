from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v5_pretrained_semantic_pair_ranker_source.ipynb"

for beta, tag in [(0.30, "beta030"), (0.10, "beta010")]:
    notebook = nbformat.read(SOURCE, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type != "code":
            continue
        text = "".join(cell.source)
        text = text.replace("LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v5'", f"LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v5_{tag}'")
        text = text.replace("Path('/kaggle/working/datathon_task2_v5')", f"Path('/kaggle/working/datathon_task2_v5_{tag}')")
        text = text.replace("LOCKED_CONFIG=3; LOCKED_BETA=.20", f"LOCKED_CONFIG=3; LOCKED_BETA={beta:.2f}")
        text = text.replace("datathon_task2_v5_semantic_pair_blend.csv", f"datathon_task2_v5_semantic_pair_blend_{tag}.csv")
        text = text.replace("datathon_task2_v5_artifacts", f"datathon_task2_v5_{tag}_artifacts")
        cell.source = text
        cell.outputs = []
        cell.execution_count = None
    client = NotebookClient(notebook, timeout=1800, kernel_name="python3", resources={"metadata": {"path": str(ROOT.parent.parent.parent)}})
    client.execute()
    run_path = ROOT / f"notebooks/runs/V5 {tag} Local Notebook.ipynb"
    nbformat.write(notebook, run_path)
    submission = ROOT / f"output/v5_{tag}/datathon_task2_v5_semantic_pair_blend_{tag}.csv"
    destination = ROOT / f"submissions/datathon_task2_v5_semantic_pair_blend_{tag}.csv"
    destination.write_bytes(submission.read_bytes())
    print(beta, destination)
