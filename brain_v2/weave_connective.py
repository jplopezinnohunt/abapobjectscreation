"""
Weave the connective layer into the EXISTING graph — incremental, fast.

Loads brain_v2_graph.json, runs the connective ingestor (USER/OPERATES_TCODE/
BELONGS_TO_PACKAGE/RUNS_PROGRAM edges from Gold DB), saves. Does NOT re-parse
code — this is how the brain grows new synapses without rebuilding the cortex.

Run:  python brain_v2/weave_connective.py
Then: python brain_v2/build_brain_state.py   (optional — brain_state is unaffected
      unless a connected object is curated; the new layers live in the graph and
      are reachable via graph_queries.py)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from brain_v2.core.graph import BrainGraph
from brain_v2.ingestors.connective_ingestor import ingest_connective
from brain_v2.ingestors.process_ingestor import ingest_processes

GOLD_DB = ROOT / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
BRAIN_JSON = ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
BRAIN_SQLITE = ROOT / "brain_v2" / "output" / "brain_v2_index.db"


def main():
    print("Weaving connective layer into existing graph...")
    brain = BrainGraph.load_json(str(BRAIN_JSON))
    n0, e0 = brain.node_count(), brain.edge_count()
    print(f"  before: {n0:,} nodes  {e0:,} edges")

    # Build the process spine FIRST (STEP -USES_TCODE-> TRANSACTION), so the
    # connective pass then wires those transactions to programs/tables/users.
    pstats = ingest_processes(brain)
    print(f"  process spine: {pstats['step_nodes']} steps, {pstats['edges']} edges (incl. STEP_USES_TCODE)")

    stats = ingest_connective(brain, str(GOLD_DB))

    n1, e1 = brain.node_count(), brain.edge_count()
    print(f"  after:  {n1:,} nodes  {e1:,} edges   (+{n1-n0:,} nodes, +{e1-e0:,} edges)")
    print()
    print("  Connected this pass:")
    print(f"    USER nodes (from bkpf.USNAM):        {stats['users']:,}")
    print(f"    USER -OPERATES_TCODE-> TRANSACTION:  {stats['operates']:,}")
    print(f"    TRANSACTION -USED_IN_CC-> COCODE:    {stats['used_in_cc']:,}")
    print(f"    PACKAGE nodes (from tadir):          {stats['packages']:,}")
    print(f"    object -BELONGS_TO_PACKAGE-> PKG:    {stats['belongs_to_package']:,}")
    print(f"    JOB -RUNS_PROGRAM-> PROGRAM:         {stats['job_runs_program']:,}")
    print(f"    TRANSACTION -EXECUTES_PROGRAM-> PROG:{stats.get('executes_program',0):,}")
    print(f"    TRANSACTION -MAINTAINS_VIEW-> TABLE: {stats.get('maintains_view',0):,}")
    print()
    print("  EXTRACTION BACKLOG (edges we WANT but the source table isn't in Gold DB yet):")
    for tbl, desc in stats["backlog"]:
        print(f"    [{tbl}]  {desc}")

    brain.save_json(str(BRAIN_JSON))
    brain.save_sqlite(str(BRAIN_SQLITE))
    print()
    print(f"  Saved: {BRAIN_JSON}")


if __name__ == "__main__":
    main()
