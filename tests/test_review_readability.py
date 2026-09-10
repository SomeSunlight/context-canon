from contextcanon.diff import ContextDiff, DiffEntry, render_diff


def test_render_diff_puts_human_summary_before_technical_fingerprints():
    diff = ContextDiff(
        node_id="node",
        before_name="Development Workflow",
        after_name="Development Workflow",
        before_version="0.2.0-draft",
        after_version="0.2.1-draft",
        before_normalized_digest="a" * 64,
        after_normalized_digest="b" * 64,
        before_package_digest="c" * 64,
        after_package_digest="d" * 64,
        entries=(
            DiffEntry("rule", "added", "node#R1", None, {"status": "active"}),
            DiffEntry("rule", "added", "node#R2", None, {"status": "active"}),
            DiffEntry("rule", "added", "node#R3", None, {"status": "active"}),
            DiffEntry("resource", "modified", "docs/change.md", {"sha256": "x"}, {"sha256": "y"}, ("sha256",)),
        ),
    )
    rendered = render_diff(diff)
    assert "Version: 0.2.0-draft -> 0.2.1-draft" in rendered
    assert "Summary: 3 rules added, 1 resource changed" in rendered
    assert rendered.index("Summary:") < rendered.index("Rules:")
    assert rendered.index("Resources:") < rendered.index("Technical details:")
    assert "Normalized digest:" in rendered
    assert "Package digest:" in rendered
