# CLAUDE BUILD SPEC — Huntington Cyber Inventory OAS

**Feed this file to Claude along with the API Standard and the Heartbeats template.**

```bash
claude "Read CLAUDE-BUILD-SPEC.md and follow it. \
        Reference files are in ./reference/."
```

Expected layout:

```
./CLAUDE-BUILD-SPEC.md                 <- this file
./QUESTION-SHEET.md                    <- open decisions, numbered Q01..Q20
./reference/API_Standard.txt           <- the API/OAS Review Checklist
./reference/HNB_ExampleHeartbeats_3.1 20250319AGW.yaml
./HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml   <- current working OAS
```

**This file is meant to be edited.** As answers arrive from Governance, update
section 2 and re-run. See section 9 for the change log convention.

---

# 1. What you are building

A **read-only (GET) microservice OAS** for a cyber inventory API that queries the
Huntington CMDB — and later a datalake — to return server and application
inventory with security posture across the fleet.

**Two collections, therefore two OAS documents.** One OAS defines one Collection;
the template hard-wires this in `info.x-hnb.collection` (a single `oas` name and a
single `resourceDefinition`) and in the response chain (every response funnels into
one `<collection>_base`). Do not attempt to put both collections in one file.

| Collection | Source table | Root path | Filter key |
|---|---|---|---|
| servers | `cmdb_ci_server` | `/cyber-inventories-servers` | `assetId` (query) |
| applications | `cmdb_ci_business_app` | `/cyber-inventories-applications` | `applicationCorrelationReference` (query) |

Later collections, already identified on the planning board and **out of scope for
v1**: application services (`cmdb_ci_service_discovered_list`), app-to-server
(`u_cmdb_app_to_server`), exception requests
(`x_thhnb_except_man_exception_request`), risk and security profile
(`u_cmdb_ci_risk_and_security-pr`).

---

# 2. Current answers — UPDATE THIS SECTION AS GOVERNANCE RESPONDS

> Anything marked `UNANSWERED` must be emitted into the OAS as an inline
> `[ANSWER-NEEDED Qnn]` comment. **Never invent a value and present it as settled.**

| Q | Decision | Value | Status |
|---|---|---|---|
| Q01 | Collection name (servers) | `cyber-inventories-servers` | **UNANSWERED — placeholder** |
| Q01 | Abbreviation | `cy-inv-srvr` | **UNANSWERED — Governance assigns** |
| **Q02** | **Classification** | **`HNB`** — confirmed by Governance 2026-08-17. Filename prefix `HNB_`, module `hnb-<abbrev>`, title starts `HNB`, no `proxyPrefix`. | **ANSWERED** |
| Q03 | Resource id source | CMDB `sys_id` (32-char GUID) | **UNANSWERED — recommended** |
| Q04 | Team CMDB correlation id / name | — | **UNANSWERED** |
| Q05 | Contact + owner + approver emails, team initials | — | **UNANSWERED** |
| Q06 | OAuth2 scope | `cy-inv-srvr:read` | **UNANSWERED** |
| Q07 | EQH or direct-to-SoR | `GCP` assumed | **UNANSWERED** |
| Q08 | Environment endpoints | — | **UNANSWERED** |
| **Q09** | **HTTP verbs** | **GET only** | **ANSWERED** |
| Q10 | Quota / call volumes | Heartbeats defaults | **UNANSWERED** |
| Q11 | Internal only | recommended yes | **UNANSWERED** |
| Q12 | `/retrieve` POST-as-GET permitted | included, flagged | **UNANSWERED** |
| Q13 | Common section copied verbatim | no — hand-written | **UNANSWERED** |
| Q14 | Partial string matching | exact assumed | **UNANSWERED** |
| Q15 | Confirmed field set | 38 `cmdb_ci_server` columns + 6 `cmdb_ci_business_app` columns identified; column names not yet supplied. **38 source columns ≠ 38 API fields** — coded columns split into `*Code` + `*Description`, some columns are not exposed, some API fields are computed and have no source column. | **PARTIAL** |
| Q16 | Non-CMDB records surfaced | `dataQuality` aggregate present | **UNANSWERED** |
| Q17 | `expand_resources` inlining | not implemented | **UNANSWERED** |
| Q18 | Enum values (8 fields) | assumed | **UNANSWERED** |
| Q19 | Sensitivity: IP, personal names | exposed + flagged | **UNANSWERED** |
| Q20 | `serialNumber` acceptable | assumed yes | **UNANSWERED** |

---

# 3. HARD RULES — every one of these is a review finding if broken

These are extracted from the API Standard. Treat them as constraints, not
suggestions. **Check each one before returning output.**

## 3.1 Structure

- `openapi: 3.0.3`
- **One OAS = one Collection.** Never two root collections in one file.
- Must validate in the SmartBear Swagger Editor. YAML only, never JSON.
- Every internal `$ref` must resolve. No dangling references.

## 3.2 Naming — collection

- Nodes separated by `-`, lower-back-bone-case in paths and schema prefixes
- Right-most token **plural**
- Second-level token **plural**
- First level **singular** when there is more than one level; plural when only one
- Example: `cyber-inventories-servers` ✔ (`cyber` singular, `inventories` plural,
  `servers` plural)

## 3.3 Naming — resource identifier

- Unique id = **singular collection name + `Id`**, dashes removed, next char upcased
  - `cyber-inventories-server` → `cyberInventoriesServerId`
- Must be `type: string`, **never a number**
- Should be a **GUID** — for opaqueness and to deny a small-namespace attack surface

## 3.4 Path parameters — THE MOST COMMONLY BROKEN RULE

> **Only the resource id of the collection may be a path parameter.
> Every other field is a query parameter.**

```
✔ GET /cyber-inventories-servers/{cyberInventoriesServerId}
✔ GET /cyber-inventories-servers?assetId=AST0012345
✘ GET /cyber-inventories-servers/{assetId}          <- REJECTED
✘ GET /servers/{assetId}                            <- REJECTED
```

## 3.5 Field naming — reserved suffixes

| Suffix | Meaning | Rule |
|---|---|---|
| `Id` | EIM collection identifier | Reserved; Governance approves |
| `Reference` | Instance **outside** an HNB collection | Use for CMDB `sys_id` cross-refs |
| `Timestamp` | ISO 8601, 32 chars | `CCYY-MM-DDTHH:MM:SS.mmmmmm+05:00` |
| `Date` | ISO 8601, 10 chars | `CCYY-MM-DD` |
| `Period` | ISO 8601 period | |
| `Indicator` | Boolean | Literal `true`/`false`. **Never** `Y/N`, `1/0`, or quoted |
| `Code` | Programmatic value | **MUST** have a matching `Description` |
| `Description` | Human-readable partner | Required in `_RESOURCE` **and** `_SUMMARY` |
| `Amount` | Monetary | Pair with `currencyCode` |

**Forbidden as suffixes:** `id`, `Identifier`, `identifier`

**Forbidden as standalone field or aggregate names:**
`status`, `statuses`, `number`, `distance`, `amount`

> This bites immediately: CMDB has `operational_status` and `install_status`.
> Rename to `operationalStatusCode` + `operationalStatusDescription`.

## 3.6 Validation keywords

- **Numbers and integers:** only `minimum`, `maximum`, `exclusiveMinimum`,
  `exclusiveMaximum`, `multipleOf`.
  **`minLength`/`maxLength` are invalid on numeric types.**
- **Strings with an `enum`:** must **NOT** carry `minLength`/`maxLength`.
- `required` may only list fields defined in that same object — never in a child.

## 3.7 operationId

Format: `<Method><CollectionName><Limiter><Set>`

- Method: `get` (this API is GET-only; `retrieve` for POST-as-GET)
- Collection name **plural** when the resource id is NOT a path parameter
- Collection name **singular** when the resource id IS a path parameter
- Limiter appended if the path has one (`Summary`)
- `<collection>/ping` → ends `Ping`; bare `/ping` → ends `PingProxy`

```
GET /cyber-inventories-servers/summary            -> getCyberInventoriesServersSummary
GET /cyber-inventories-servers                    -> getCyberInventoriesServers
GET /cyber-inventories-servers/{id}/summary       -> getCyberInventoriesServerSummary
GET /cyber-inventories-servers/{id}               -> getCyberInventoriesServer
GET /cyber-inventories-servers/ping               -> getCyberInventoriesServersPing
GET /ping                                         -> getCyberInventoriesServersPingProxy
```

## 3.8 Tags

- **Plural** stylized name → collection operations
- **Singular** → single-resource operations
- `<Collection Name> (set)` → multi-resource PUT/PATCH/DELETE — **not used here**, GET only

## 3.9 Security

- The default security stanza applies to **ALL** operations. **Do not override per
  operation** (rule effective 2023-05-22).
- Must include: `Auth_correlationId` (query `_correlationId`),
  `Auth_originatingChannel` (`X-HNB.originatingChannel`),
  `Auth_requestingChannel` (`X-HNB.requestingChannel`), `Auth_Bearer`.
- `_correlationId` is **REQUIRED on every call including GET**. Logging and tracing
  depend on it.

## 3.10 Scopes

- `info.x-hnb.scopes` = union of every scope used in the document
- Each operation carries only the scopes it needs
- `/<collection>/ping` → the prevailing `:read` scope
- **`/ping` → `[""]` — DO NOT MODIFY**

## 3.11 Schema hierarchy — reproduce exactly

```
HTTP_200                    -> Response                    -> <collection>_base
HTTP_200_summary            -> Response_summary            -> <collection>_base_summary
HTTP_200_collection         -> Response_collection         -> <collection>_base
HTTP_200_collection_summary -> Response_collection_summary -> <collection>_base_summary
HTTP_200_EXPANDEDRESOURCE   -> Response_EXPANDEDRESOURCE   -> <collection>_base_EXPANDEDRESOURCE

<collection>_base*  ->  _RESOURCE | _SUMMARY | _EXPANDEDRESOURCE
```

- Every collection-specific schema is prefixed `<lower-back-bone-collection>_`
- **`_RESOURCE` must END with `_metadata: $ref __common_metadata_included`.**
  Nothing after it.
- `_SUMMARY` must be a **strict subset** of `_RESOURCE`, and any field that lives
  inside an aggregate in `_RESOURCE` must stay inside that same aggregate in
  `_SUMMARY`.

## 3.12 Query parameters

> **Every query parameter must be a field that exists in `_RESOURCE` or in the
> metadata.** You cannot filter on a field you have not exposed.

Permitted variants:
- `show_<aggregate>` — controls whether an aggregate in `_RESOURCE` is returned
- `<field>_min` / `<field>_max` — inclusive range bounds

## 3.13 Responses

- Every operation needs at least a `200` and a `default`
- Document only codes this service can actually produce
- Codes beyond the Heartbeats set require Governance approval
- A collection search with no matches is **`200` with an empty array — never `404`**
- `404` is only correct for single-resource operations

## 3.14 The common section

> *"AVOID changing (i.e. DO NOT change) anything from here to 'common components
> and responses END'."*

Copy the `__common_*` block **verbatim** from the current Heartbeats template.
Do not hand-author it, do not tidy it, do not "improve" it.

## 3.15 Filename and module

| Classification | Filename | Module | Title |
|---|---|---|---|
| HNB | `HNB_<Collection>_<Ver> <CCYYMMDD>-<Init>.yaml` | `hnb-<abbrev>` | `Huntington <Collection Name> API` |
| Orchestration | `Orch_<Collection>_<Ver> <CCYYMMDD>-<Init>.yaml` | `orch-<abbrev>` | `Orchestration / Composite <Collection> API` |
| Application | `App_<AppName>-<Collection>_<Ver> <CCYYMMDD>-<Init>.yaml` | `app-<appname>-<abbrev>` | `Application <Abbrev> <Collection Name> API` |

- Version in filename and module is **major.minor** only
- `info.version` is **major.minor.patch**
- File date must match the version of the file being submitted


## 3.16 YAML that every parser accepts — DO NOT COPY THE TEMPLATE'S STYLE

The reference template does not parse. Verified, not suspected:

| Defect | Occurrences in the template | Who rejects it |
|---|---|---|
| Tab characters in indentation | 140 lines | **every YAML parser** — the file cannot be loaded at all |
| `key:{` — no space after the colon in a flow mapping | 35 lines | `openapi-spec-validator` |
| Flow collection wrapped onto a continuation line indented to the parent's column | 12 lines | **js-yaml — the parser Swagger Editor runs on** |

PyYAML accepts the last two, which is exactly why they survive: the file loads
in Python, gets committed, and fails at submission when a reviewer pastes it
into Swagger Editor.

Rules, therefore:

1. **Never emit a tab character.** Indentation is spaces only.
2. **Always put a space after a colon**, including inside flow mappings.
3. **Never wrap a flow collection across lines.** If it does not fit on one
   line, write it in block style instead. `servers[].variables` in this OAS is
   block style for exactly this reason.
4. **Never paste a JSON example block in as-is.** That is where the template's
   tabs come from. Re-indent it with spaces, or write it as YAML.
5. Line endings are LF. A `.gitattributes` with `*.yaml text eol=lf` keeps a
   Windows checkout from reintroducing CRLF.

`scripts/validate_oas.py` enforces 1–3 and runs them *before* the parse check,
so a tab is reported as "no tab characters: FAIL, line 2085" rather than as an
unexplained parse error.

---

# 4. How to handle unanswered decisions

**Do not guess silently.** When a value is unknown:

1. Use a clearly-marked placeholder that keeps the document valid
2. Add an inline comment: `# [ANSWER-NEEDED Qnn] <what is needed and why it matters>`
3. If it is a new question not yet in `QUESTION-SHEET.md`, append it there with the
   next number and state who should answer it

The document must always satisfy:

```bash
python3 -c "import yaml;yaml.safe_load(open('<file>.yaml'))"   # parses
grep -c "ANSWER-NEEDED" <file>.yaml                             # > 0 until complete, 0 at submission
```

**A placeholder that is flagged is fine. A guess that looks settled is not** — it
will be reviewed as though someone decided it, and nobody did.

---

# 5. Field mapping procedure

For every candidate CMDB column, decide **expose / omit / rename / split**, then
apply the naming rules. Work down this list:

1. Is it a boolean? → suffix `Indicator`, type `boolean`, literal `true`/`false`
2. Is it a coded value? → split into `<name>Code` **+** `<name>Description`
3. Is it a timestamp? → suffix `Timestamp`, ISO 8601, `maxLength: 32`
4. Is it a date only? → suffix `Date`, ISO 8601, `maxLength: 10`
5. Does it point outside this collection? → suffix `Reference`
6. Is the name a forbidden standalone word? → rename (`status` → `operationalStatusCode`)
7. Does it end in a forbidden suffix (`id`, `Identifier`)? → rename
8. Is it sensitive (IP, personal name, credential)? → flag for Q19 review
9. Does anyone actually need it? → **if no, omit it.** Every exposed field is
   surface area, a filter you may be asked to support, and a field you must keep
   populated.

### Worked examples

| CMDB column | Compliant name | Why |
|---|---|---|
| `sys_id` | `cyberInventoriesServerId` | Resource id; GUID |
| `name` | `serverName` | |
| `operational_status` | `operationalStatusCode` + `operationalStatusDescription` | `status` forbidden standalone; Code needs Description |
| `install_status` | `installStatusCode` + `installStatusDescription` | same |
| `virtual` | `virtualIndicator` | boolean → Indicator |
| `sys_updated_on` | `lastUpdatedTimestamp` | ISO 8601, 32 chars |
| `warranty_expiration` | `warrantyExpirationDate` | date only, 10 chars |
| `u_correlation_id` | `applicationCorrelationReference` | points outside the collection |
| `ip_address` | `infrastructure.ipAddress` | **flag Q19 sensitivity** |
| `cpu_core_count` | `cpuCoreCount` | integer: `minimum`/`maximum` only |
| `short_description` | `description` | |

### Aggregate grouping used in the servers OAS

`infrastructure` · `ownership` · `lifecycle` · `riskAndSecurity` · `vulnerability` ·
`dataQuality`

Each aggregate gets a matching `show_<aggregate>` query parameter.

**`dataQuality` is not optional decoration.** It exists because the CMDB is
explicitly not the source of truth for everything. Without it the API reports
"we have no record" and "the attribute is genuinely empty" identically — a silent
wrong answer, which is the worst failure mode a security inventory can have.

---

# 6. Validation — run before returning any output

There is one command. Run it. Do not hand back an OAS you have not run it on.

```bash
python3 scripts/validate_oas.py HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
```

Exit codes:

| Code | Meaning |
|---|---|
| `0` | every enforced rule passes |
| `1` | at least one rule FAILED — the file is not submittable |
| `2` | `--strict` was used and unresolved `[ANSWER-NEEDED]` / `PLACEHOLDER` markers remain |

It enforces 24 rules: no tabs, flow-mapping spacing, single-line flow
collections, parses, OpenAPI version, every internal `$ref` resolves, exactly
one root collection, collection naming, only the resource id is a path
parameter, numeric keyword rules, enum keyword rules, `*Code`/`*Description`
pairing, forbidden standalone names, forbidden `id`/`Identifier` suffixes,
`_RESOURCE` ends with `_metadata`, `_SUMMARY` is a strict subset of `_RESOURCE`,
operationId convention, every query parameter exists in `_RESOURCE`, `/ping`
scope is `[""]`, `<collection>/ping` uses the `:read` scope, every operation has
`200` and `default`, a global security stanza exists, security is never
overridden per operation, and `info.x-hnb.scopes` is the union of every
operation's scopes.

Then run the structural check, which answers a different question — the
validator asks "does this follow the HNB standard", this asks "is this valid
OpenAPI 3.0":

```bash
pip install openapi-spec-validator
python3 -m openapi_spec_validator HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
```

Both run automatically on every push via `.github/workflows/oas-governance.yml`.
The `check` job tolerates open markers, because a contract with open questions
is the normal state of work in progress. The `gate` job adds `--strict` and runs
only on the `submission` branch and on `v*` tags, so the file cannot be handed
to Governance with an unanswered question still in it.

**What the validator cannot do.** It cannot check judgement: whether
`cyber-inventories-servers` is the right collection name, whether a field
should be exposed at all, whether an enum matches what CMDB actually stores.
Those need Governance and a human. The point of automating the mechanical rules
is that human review gets spent on the decisions that actually need a person.

Still confirm by reading:

- [ ] Field *meanings* match the CMDB columns they came from
- [ ] Enum values match what the source system actually stores
- [ ] Descriptions say what the field is *for*, not what its type is
- [ ] Every assumption you made is marked `[ANSWER-NEEDED]`, not silently settled

---

# 7. Generating the applications collection

The applications OAS is the servers OAS with substitutions — **not a rewrite**.

```bash
sed -e 's/cyber-inventories-servers/cyber-inventories-applications/g' \
    -e 's/cyberInventoriesServers/cyberInventoriesApplications/g' \
    -e 's/cyberInventoriesServerId/cyberInventoriesApplicationId/g' \
    -e 's/Cyber Inventories Servers/Cyber Inventories Applications/g' \
    -e 's/Cyber Inventories Server/Cyber Inventories Application/g' \
    -e 's/cy-inv-srvr/cy-inv-app/g' \
    HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml \
  > HNB_Cyber-inventories-applications_1.0_PLACEHOLDER.yaml
```

Then **by hand**:

1. Replace the entire field set with application fields from `cmdb_ci_business_app`
2. Replace the aggregates — `infrastructure` and `vulnerability` do not apply to an
   application; likely aggregates are `ownership`, `lifecycle`, `riskAndSecurity`,
   `dataQuality`, and possibly `hosting` (the app-to-server relationship)
3. Change the primary filter from `assetId` to `applicationCorrelationReference`
4. Re-check `_SUMMARY` is a strict subset of the **new** `_RESOURCE`
5. Update `info.description`
6. **Run the full section 6 validation again.** A sed-generated file that has not
   been validated is not a deliverable.

**Do not** let the substitution leave server-specific fields (`cpuCoreCount`,
`operatingSystemName`, `ipAddress`) in the applications resource. That is the most
likely failure mode of this procedure.

---

# 8. Ground rules for the model

1. **Never invent a Governance-owned value.** Collection names, abbreviations,
   scopes, and correlation ids come from Governance. Emit `[ANSWER-NEEDED]`.
2. **Never break a hard rule in section 3 for convenience.** If a request conflicts
   with a rule, say so and cite the rule rather than complying.
3. **Prefer omitting a field to guessing its enum.** A field with an invented enum
   looks decided.
4. **Every change must keep the file valid.** Run section 6 before returning.
5. **State what you changed and why.** A diff nobody can explain is a diff nobody
   can review.
6. **When the standard and the request disagree, flag it.** The request to make
   `GET /servers/{assetId}` work is the live example: it is a reasonable-sounding
   design that the standard explicitly rejects, and quietly implementing it would
   have produced a rework cycle.

---

# 9. Change log

Append a row whenever this spec is updated. The spec is the contract between the
team and the model; an undocumented change to it is an undocumented change to
every OAS generated afterwards.

| Date | Change | By |
|---|---|---|
| 2026-08-16 | Initial. Sections 1–9, Q01–Q20, servers OAS at 1786 lines validating clean. | — |
| 2026-08-17 | Q02 ANSWERED — Governance classifies this as `HNB`. Q15 moved to PARTIAL (field counts known, column names outstanding). | — |
| 2026-08-17 | Added rule 3.16 (YAML portability) after finding the reference template contains 140 tabbed lines and does not parse. Rewrote `servers[].variables` in block style. | — |
| 2026-08-17 | Section 6 replaced with `scripts/validate_oas.py` (24 rules) plus `openapi-spec-validator`; both wired into `.github/workflows/oas-governance.yml`. | — |
