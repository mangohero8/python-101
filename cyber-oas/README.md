# Cyber Inventory OAS — Working Bundle

| File | What it is | Who reads it |
|---|---|---|
| `HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml` | The OAS. 1,849 lines, passes all 24 governance checks, 40 inline open decisions | You, then Governance |
| `QUESTION-SHEET.md` | Every open decision Q01–Q20, grouped by who answers it | You → Governance, CMDB owners, Cyber Architecture |
| `CLAUDE-BUILD-SPEC.md` | Machine-followable spec for generating/updating the OAS with Claude CLI | The class, and Claude |
| `scripts/validate_oas.py` | The API standard, written as 24 executable checks | Everyone — run it before every commit |
| `.github/workflows/oas-governance.yml` | Runs the validator on every push; blocks submission while questions are open | CI |
| `OAS-READINESS-REVIEW.md` | Why the original plan conflicts with the standard, with recommendations | Anyone asking "why did we change the paths?" |

## Start here

```bash
# validate — this is the only command you need to remember
python3 scripts/validate_oas.py HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml

# what is still open
grep -n "ANSWER-NEEDED" HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
```

Requires `pip install pyyaml`. For the structural check as well:

```bash
pip install openapi-spec-validator
python3 -m openapi_spec_validator HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
```

The two answer different questions. The validator asks *does this follow the
Huntington standard*. `openapi-spec-validator` asks *is this valid OpenAPI 3.0*.
A file can pass either one and fail the other.

## Using it with Claude CLI

```
project/
├── CLAUDE-BUILD-SPEC.md
├── QUESTION-SHEET.md
├── HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
├── scripts/validate_oas.py
└── reference/
    ├── API_Standard.txt
    └── HNB_ExampleHeartbeats_3.1_20250319AGW.yaml
```

```bash
claude "Read CLAUDE-BUILD-SPEC.md and follow it. Reference files are in ./reference/.
Run scripts/validate_oas.py before you hand anything back."
```

As answers arrive, update **section 2** of `CLAUDE-BUILD-SPEC.md` and re-run.
That table is the single source of truth for what has been decided.

## Current state

- 8 paths, 8 operations, 96 schemas, 29 parameters, 12 responses
- 136 internal `$ref`s, all resolving
- 24/24 governance checks pass; valid OpenAPI 3.0.3
- 40 `[ANSWER-NEEDED]` markers, 29 `PLACEHOLDER` values
- **Not submittable until both counts reach zero** — the `gate` CI job enforces this

## Known defect in the reference template

The `HNB_ExampleHeartbeats_3.1` template we were given **does not parse in any
YAML parser.** It contains 140 lines indented with tab characters, from JSON
example blocks pasted in with their original indentation. It also uses two flow
mapping styles that Swagger Editor and `openapi-spec-validator` reject.

None of that is visible if you load it in Python — PyYAML is lenient about two
of the three. Copy example blocks out of that file with care, and run the
validator afterwards. Rule 3.16 in the build spec has the detail; the validator
enforces it.

## The four blockers

| # | Question | Owner |
|---|---|---|
| Q01 | Approved collection name + abbreviation | API Governance |
| ~~Q02~~ | ~~Classification~~ — **answered: HNB** | ~~API Governance~~ |
| Q03 | Resource identifier — `sys_id`, and is it a GUID? | API Governance |
| Q13 | Common section copied verbatim from current Heartbeats | API Governance |
| Q15 | The 38 `cmdb_ci_server` + 6 `cmdb_ci_business_app` column names | CMDB owners |
