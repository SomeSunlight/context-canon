from pathlib import Path

helper = Path("tools/_block_r6_source_step3.py")
text = helper.read_text(encoding="utf-8")
old = '    fast_scope = "- **Scope:** corrections discovered while vertically reviewing the real `ai-workstation` onboarding placement, through the next coherent owner-review candidate."\n'
new = '    fast_scope = "- **Scope:** corrections discovered while vertically reviewing the real onboarding placement, through the next coherent owner-review candidate."\n'
if text.count(old) != 1:
    raise SystemExit(f"Block R completion scope anchor count {text.count(old)}")
helper.write_text(text.replace(old, new, 1), encoding="utf-8")
