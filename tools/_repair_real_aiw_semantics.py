from pathlib import Path

path = Path("tools/_real_aiw_review.py")
text = path.read_text(encoding="utf-8")
old = '''item(3,"Local model integration deferred","plan","promote","N-001","The evidence explicitly marks this as later work; the owner removed the speculative reserved Node from structure, so the plan stays project-level.",[ev("README.md",5,8)],{"text":"Local model integration is intentionally deferred to the next phase.","wording_origin":"exact"}),'''
new = '''item(3,"Local model integration deferred","plan","promote","N-001","The frozen Evidence explicitly marks this as later work, while the accepted structure has no dedicated local-model Node; keep the reviewed plan visible at project level.",[ev("README.md",5,8)],{"text":"Local model integration is intentionally deferred to the next phase.","wording_origin":"exact"}),'''
if text.count(old) != 1:
    raise SystemExit(f"P003 target count={text.count(old)}")
text = text.replace(old, new, 1)
old = '''item(32,"Supported host baseline","state","promote","N-001","The supported platform list describes current compatibility state that may evolve.",[ev("README.md",337,345)],{"text":"Supported host: Windows 11 with current Store WSL; PowerShell 7.4 or newer; Ubuntu 24.04 under WSL 2; x86-64 Windows and WSL architecture.","wording_origin":"lightly-edited"}),'''
new = '''item(32,"Supported host baseline","state","promote","N-001","The supported platform list describes current compatibility state that may evolve.",[ev("README.md",348,353)],{"text":"Supported host: Windows 11 with current Store WSL; PowerShell 7.4 or newer; Ubuntu 24.04 under WSL 2; x86-64 Windows and WSL architecture.","wording_origin":"lightly-edited"}),'''
if text.count(old) != 1:
    raise SystemExit(f"P032 target count={text.count(old)}")
path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")
