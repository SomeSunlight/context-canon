from pathlib import Path

path = Path(__file__).with_name("issue27_propagation_ux.py")
text = path.read_text(encoding="utf-8")

old_start = "TEST.write_text(r'''"
if text.count(old_start) != 1:
    raise SystemExit("unexpected test-string opener")
text = text.replace(old_start, 'TEST.write_text(r"""', 1)
old_end = "''', encoding=\"utf-8\")"
pos = text.rfind(old_end)
if pos < 0:
    raise SystemExit("unexpected test-string closer")
text = text[:pos] + '""", encoding="utf-8")' + text[pos + len(old_end):]

old_match = '''text = replace_once(
    text,
    ''' + "'''" + '''                parsed = parse_node(node_root, repo_root)\n                current = next(source for source in parsed.sources if source.id == source_id)\n                if args.source_command == \"update\":\n''' + "'''" + ''',
    ''' + "'''" + '''                if args.source_command == \"update\":\n''' + "'''" + ''',
    "remove duplicate source parse",
)
'''
new_match = '''duplicate_parse = ''' + "'''" + '''                parsed = parse_node(node_root, repo_root)\n                current = next(source for source in parsed.sources if source.id == source_id)\n                if args.source_command == \"update\":\n''' + "'''" + '''
first = text.index(duplicate_parse)
second = text.index(duplicate_parse, first + len(duplicate_parse))
text = text[:second] + ''' + "'''" + '''                if args.source_command == \"update\":\n''' + "'''" + ''' + text[second + len(duplicate_parse):]
'''
if text.count(old_match) != 1:
    raise SystemExit(f"unexpected duplicate-parse applicator block: {text.count(old_match)}")
text = text.replace(old_match, new_match, 1)

path.write_text(text, encoding="utf-8")
