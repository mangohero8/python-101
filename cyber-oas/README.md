# Cyber Inventory OAS — Working Bundle

| File | What it is | Who reads it |
|---|---|---|
| `HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml` | The OAS. 1,786 lines, validates clean, 42 inline open decisions | You, then Governance |
| `QUESTION-SHEET.md` | Every open decision Q01–Q20, grouped by who answers it | You → Governance, CMDB owners, Cyber Architecture |
| `CLAUDE-BUILD-SPEC.md` | Machine-followable spec for generating/updating the OAS with Claude CLI | The class, and Claude |
| `OAS-READINESS-REVIEW.md` | Why the original plan conflicts with the standard, with recommendations | Anyone asking "why did we change the paths?" |

## Start here

```bash
# what is still open
grep -n "ANSWER-NEEDED" HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml

# validate after any edit
python3 -c "import yaml;yaml.safe_load(open('HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml'));print('valid')"
```

## Using it with Claude CLI

```
project/
├── CLAUDE-BUILD-SPEC.md
├── QUESTION-SHEET.md
├── HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
└── reference/
    ├── API_Standard.txt
    └── HNB_ExampleHeartbeats_3.1 20250319AGW.yaml
```

```bash
claude "Read CLAUDE-BUILD-SPEC.md and follow it. Reference files are in ./reference/."
```

As answers arrive, update **section 2** of `CLAUDE-BUILD-SPEC.md` and re-run.
That table is the single source of truth for what has been decided.

## Current state

- 8 paths, 8 operations, 96 schemas, 29 parameters, 12 responses
- 136 internal `$ref`s, all resolving
- 42 `[ANSWER-NEEDED]` markers, 23 `PLACEHOLDER` values
- **Not submittable until both counts reach zero**

## The four blockers

| # | Question | Owner |
|---|---|---|
| Q01 | Approved collection name + abbreviation | API Governance |
| Q02 | Classification: HNB / Orch / App | API Governance |
| Q03 | Resource identifier — `sys_id`, and is it a GUID? | API Governance |
| Q13 | Common section copied verbatim from current Heartbeats | API Governance |
