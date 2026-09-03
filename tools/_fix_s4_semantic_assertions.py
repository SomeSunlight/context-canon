from pathlib import Path

p = Path("tools/_block_s_machine_state_step4.py")
text = p.read_text(encoding="utf-8")
old = r'''        goose = Compiler(repo).compile(repo / "compose/goose")
        goose_rule_ids = {rule.id for rule in (*goose.inherited_rules, *goose.local_rules)}
        self.assertIn("CCW-006", goose_rule_ids)
        self.assertIn("P-001", goose_rule_ids)
        self.assertIn("P-004", goose_rule_ids)
        self.assertIn("P-005", goose_rule_ids)
        self.assertNotIn("P-002", goose_rule_ids)
        self.assertNotIn("P-003", goose_rule_ids)
        self.assertNotIn("P-006", goose_rule_ids)
        self.assertIn("CCW-TOPIC-CHANGE-WORKFLOW", {topic.id for topic in goose.inherited_topics})
'''
new = r'''        goose = Compiler(repo).compile(repo / "compose/goose")
        goose_rule_ids = {rule.id for rule in (*goose.inherited_rules, *goose.local_rules)}
        goose_statements = {rule.statement for rule in (*goose.inherited_rules, *goose.local_rules)}
        self.assertIn("CCW-006", goose_rule_ids)
        self.assertEqual(
            goose_statements,
            {
                "Keep a review PR open until the project owner explicitly approves the reviewed result.",
                "AI Workstation root policy.",
                "Application runtime policy.",
                "Goose policy.",
            },
        )
        self.assertIn("CCW-TOPIC-CHANGE-WORKFLOW", {topic.id for topic in goose.inherited_topics})
'''
if text.count(old) != 1:
    raise SystemExit(f"goose assertion block count: {text.count(old)}")
text = text.replace(old, new, 1)
old = r'''        ansible = Compiler(repo).compile(repo / "bootstrap/ansible")
        ansible_rule_ids = {rule.id for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        self.assertIn("CCW-006", ansible_rule_ids)
        self.assertIn("P-001", ansible_rule_ids)
        self.assertIn("P-002", ansible_rule_ids)
        self.assertIn("P-003", ansible_rule_ids)
        self.assertNotIn("P-004", ansible_rule_ids)
        self.assertNotIn("P-005", ansible_rule_ids)
'''
new = r'''        ansible = Compiler(repo).compile(repo / "bootstrap/ansible")
        ansible_rule_ids = {rule.id for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        ansible_statements = {rule.statement for rule in (*ansible.inherited_rules, *ansible.local_rules)}
        self.assertIn("CCW-006", ansible_rule_ids)
        self.assertEqual(
            ansible_statements,
            {
                "Keep a review PR open until the project owner explicitly approves the reviewed result.",
                "AI Workstation root policy.",
                "Bootstrap policy.",
                "Ansible host policy.",
            },
        )
'''
if text.count(old) != 1:
    raise SystemExit(f"ansible assertion block count: {text.count(old)}")
text = text.replace(old, new, 1)
p.write_text(text, encoding="utf-8")
