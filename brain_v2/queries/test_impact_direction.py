"""
Regression test: impact direction must be REVERSE for forward edges.

If A --READS_TABLE--> B, changing B breaks A.
So impact_analysis("B") must find A, not vice versa.

This test exists because Session #040 shipped impact analysis with the
direction wrong (forward traversal instead of reverse). It was caught
manually, but should never happen again.
"""

from brain_v2.core.graph import BrainGraph
from brain_v2.queries.impact import impact_analysis


def test_impact_direction():
    """A reads B → changing B must impact A."""
    brain = BrainGraph()
    brain.add_node("CLASS:A", "ABAP_CLASS", "A", domain="TEST", layer="code")
    brain.add_node("TABLE:B", "SAP_TABLE", "B", domain="TEST", layer="data")
    brain.add_edge("CLASS:A", "TABLE:B", "READS_TABLE",
                   evidence="test", confidence=1.0)

    # Changing TABLE:B should impact CLASS:A
    result = impact_analysis(brain, "TABLE:B")
    affected_ids = [a["node_id"] for a in result["affected"]]
    assert "CLASS:A" in affected_ids, \
        f"Impact of TABLE:B should find CLASS:A but got {affected_ids}"

    # Changing CLASS:A should NOT impact TABLE:B (code doesn't break tables)
    result2 = impact_analysis(brain, "CLASS:A")
    affected_ids2 = [a["node_id"] for a in result2["affected"]]
    assert "TABLE:B" not in affected_ids2, \
        f"Impact of CLASS:A should NOT find TABLE:B but got {affected_ids2}"

    print("[PASS] Impact direction correct: changing table impacts reader, not vice versa")


def test_badi_backward_direction():
    """A implements BAdI B → changing B affects A."""
    brain = BrainGraph()
    brain.add_node("CLASS:IMPL", "ABAP_CLASS", "IMPL", domain="TEST", layer="code")
    brain.add_node("ENHANCEMENT:BADI", "ENHANCEMENT", "BADI", domain="TEST", layer="code")
    brain.add_edge("CLASS:IMPL", "ENHANCEMENT:BADI", "IMPLEMENTS_BADI",
                   evidence="test", confidence=1.0)

    # Changing BADI should impact IMPL (backward edge)
    result = impact_analysis(brain, "ENHANCEMENT:BADI")
    affected_ids = [a["node_id"] for a in result["affected"]]
    assert "CLASS:IMPL" in affected_ids, \
        f"Impact of BADI should find IMPL but got {affected_ids}"

    print("[PASS] BAdI backward impact correct")


def test_chain_propagation():
    """DMEE tree → class → table: changing table impacts class AND tree."""
    brain = BrainGraph()
    brain.add_node("DMEE:TREE", "DMEE_TREE", "TREE", domain="FI", layer="config")
    brain.add_node("CLASS:EXIT", "ABAP_CLASS", "EXIT", domain="FI", layer="code")
    brain.add_node("TABLE:FPAYP", "SAP_TABLE", "FPAYP", domain="FI", layer="data")

    brain.add_edge("DMEE:TREE", "CLASS:EXIT", "CONFIGURES_FORMAT",
                   evidence="test", confidence=1.0)
    brain.add_edge("CLASS:EXIT", "TABLE:FPAYP", "READS_TABLE",
                   evidence="test", confidence=1.0)

    # Changing FPAYP should impact EXIT (depth 1) and TREE (depth 2)
    result = impact_analysis(brain, "TABLE:FPAYP")
    affected_ids = [a["node_id"] for a in result["affected"]]
    assert "CLASS:EXIT" in affected_ids, "FPAYP change should impact EXIT class"
    assert "DMEE:TREE" in affected_ids, "FPAYP change should propagate to DMEE tree"

    print("[PASS] Chain propagation: table -> class -> DMEE tree")


if __name__ == "__main__":
    test_impact_direction()
    test_badi_backward_direction()
    test_chain_propagation()
    print("\nAll impact direction tests passed.")
