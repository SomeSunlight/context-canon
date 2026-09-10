from pathlib import Path

path = Path(__file__).with_name("apply_issue27_propagation_narrative.py")
text = path.read_text(encoding="utf-8")
old = '        print(f"\\\\nReview {index}/{len(edges)} — Child: {child.metadata.name} ({child_label})")\n'
new = '        print("")\n        print(f"Review {index}/{len(edges)} — Child: {child.metadata.name} ({child_label})")\n'
if text.count(old) != 1:
    raise SystemExit(f"expected one propagation newline target, found {text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
