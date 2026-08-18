# OAS Readiness Review — Cyber Inventory Microservice

Review of the API Standard, the HNB_ExampleHeartbeats_3.1 template, and the
planning boards, against the stated plan (`/servers` by asset id,
`/applications` by correlation id, sourced from CMDB and later a datalake).

**Bottom line:** the plan as described conflicts with the governance standard
in four places. All four are fixable, but three of them change the *filename,
module name, and title* — so they must be settled before a line of YAML is
written, not after.

---

# Part 1 — Blocking conflicts

## 1.1 One OAS defines ONE Collection. You have described two.

This is the biggest one.

The template hard-wires a single collection throughout:

```yaml
info:
  x-hnb.collection:
   - oas: "example-heartbeats"          # ONE collection name
   - code: "exampleHeartbeats"
   - resourceDefinition:
      $ref: "#/components/schemas/example-heartbeats_RESOURCE"   # ONE resource
```

And every response schema funnels into that one collection:

```
HTTP_200 → Response → payload → example-heartbeats_base → example-heartbeats_RESOURCE
```

The filename (`HNB_<Collection>_<Version>`), the module name
(`hnb-<abbreviated-collection-name>`), and the title
(`Huntington <Collection Name> API`) are all singular too.

**Putting `/servers` and `/applications` as two root collections in one OAS
has no supported representation in this template.**

### Options

| Option | Shape | Trade-off |
|---|---|---|
| **A. Two OAS documents** | `cyber-inventories-servers` and `cyber-inventories-applications`, two modules, two deployments | Standards-clean. Two of everything. Most likely what Governance expects. |
| **B. One collection, servers as the resource** | Collection is servers; applications referenced by id as a related collection | One API now, but applications become second-class — you cannot `GET /applications` |
| **C. One parent collection with sub-resources** | e.g. `cyber-inventories` where servers/applications are aggregates inside `_RESOURCE` | Fits one OAS, but `GET /servers/{id}` is then illegal — see 1.2 |

**Recommendation: A.** It matches the standard, it matches the Enterprise
Information Model approach, and the sticky-note grid on your board (six CMDB
tables × single record / all records / filtered list) already implies several
collections rather than one. Ask Governance to confirm before building.

---

## 1.2 `GET /servers/{assetId}` is not a legal path under the standard

Two rules collide with this:

> **ReST: Is the resource ID the only field that is used as a path parameter?**
> Only the resource id of the collection can be used as a path parameter in any
> of the operations within the OAS. All other fields needed to filter the
> result set should be query parameters.

> Collection name is plural of Resource name. **Unique identifier is Resource
> name plus "Id"**. Remove dashes and upcase next letter (lowerCamelCaseId).

So for a collection named `cyber-inventories-servers`, the ONLY legal path
parameter is `cyberInventoriesServerId`. The standard's own worked example
spells out that this exact pattern is wrong:

```
Incorrect
GET /customer-relationships-accounts/{accountId}   <- accountId is a path parameter
Correct
GET /customer-relationships-accounts?accountId=98765   <- accountId is a query parameter
```

By that rule, `assetId` and `correlationId` belong in the **query string**, not
the path.

### There is also a GUID requirement

> In nearly all cases, the unique identifier should be a GUID so as to ensure
> opaqueness AND provide a security defense against an attack vector of a small
> namespace.

CMDB `sys_id` **is** a 32-character GUID, so it satisfies this naturally.
A human-assigned asset tag or a numeric correlation id likely does not.

### Options

| Option | Result |
|---|---|
| **A. `sys_id` is the resource id; asset id is a query filter** | `GET /…-servers/{cyberInventoriesServerId}` + `GET /…-servers?assetId=X`. Fully compliant. |
| **B. Ask Governance to bless `assetId` as the collection identifier** | Keeps your intended shape, needs an approved exception and probably fails the GUID test |
| **C. Name the collection so its id IS the asset id** | Contrived; the EIM naming rules will fight you |

**Recommendation: A.** It costs you nothing functionally — callers who have an
asset id do one query instead of one path lookup — and it is the difference
between a clean self-approval and a rework.

---

## 1.3 Classification: is this HNB, Orchestration, or App?

This changes the filename, module, and title. From the standard:

> **Orchestration/Composite API:** APIs that span multiple domains … **This
> typically DOES NOT have its own data store** and instead is orchestrating
> across other domains that DO have a data store.

Your service queries CMDB (ServiceNow is the SoR) and later a datalake, and
holds no authoritative data of its own. **That is the textbook definition of an
Orchestration API.**

| Classification | Filename | Module | Title |
|---|---|---|---|
| HNB | `HNB_<Collection>_<Ver> <CCYYMMDD>-<Initials>.yaml` | `hnb-<abbrev>` | `Huntington <Collection> API` |
| **Orchestration** | `Orch_<Collection>_<Ver> <CCYYMMDD>-<Initials>.yaml` | `orch-<abbrev>` | `Orchestration / Composite <Collection> API` |
| App | `App_<AppName>-<Collection>_<Ver> …` | `app-<appname>-<abbrev>` | `Application <Abbrev> <Collection> API` |

**This is a question for API Governance, not a judgment call.** If the cyber
inventory is intended to become a system of *reference* in its own right
(with its own enriched, curated data), HNB may be right. If it is a read-through
to CMDB, it is Orchestration.

---

## 1.4 CMDB field names will fail the modeling rules

CMDB columns will not survive contact with the standard unmodified.

**Reserved words that cannot be standalone field names:**
`status` (or `statuses`), `number`, `distance`, `amount`

CMDB server records are full of `status`, `install_status`, `operational_status`.
Every one needs renaming.

**Mandatory suffix rules:**

| Suffix | Meaning | Consequence |
|---|---|---|
| `Id` | Unique identifier for an EIM collection | Reserved — Governance approves these |
| `Indicator` | Boolean, `true`/`false` only | Not `Y/N`, not `1/0`, not quoted |
| `Timestamp` | ISO 8601, 32 chars | `CCYY-MM-DDTHH:MM:SS.mmmmmm+05:00` |
| `Date` | ISO 8601, 10 chars | `CCYY-MM-DD` |
| `Code` | Programmatic identifier | **Must have a matching `Description`** |
| `Description` | Human-friendly text | Required in `_RESOURCE` and `_SUMMARY` |
| `Reference` | Instance outside an HNB collection | Useful for CMDB `sys_id` cross-refs |

Forbidden: `id`, `Identifier`, `identifier` as suffixes.

**Worked example — a CMDB server row translated:**

| CMDB column | Compliant field |
|---|---|
| `name` | `serverName` |
| `sys_id` | resource id (`cyberInventoriesServerId`) |
| `operational_status` | `operationalStatusCode` **+** `operationalStatusDescription` |
| `install_status` | `installStatusCode` **+** `installStatusDescription` |
| `virtual` (true/false) | `virtualIndicator` |
| `sys_updated_on` | `lastUpdatedTimestamp` |
| `warranty_expiration` | `warrantyExpirationDate` |
| `ip_address` | `ipAddressReference` or `ipAddress` — confirm with Governance |
| `u_correlation_id` | `applicationCorrelationReference` |

**This mapping is the single biggest piece of unglamorous work in the whole
contract, and it is where a review will find the most findings.**

---

# Part 2 — What the template requires that is easy to miss

Checklist of scaffolding that must be present, copied from Heartbeats:

- [ ] `/ping` — scopes set to `""`, **do not modify**
- [ ] `/<collection>/ping` — scopes set to the prevailing `:read` scope
- [ ] Security stanza used as the **default for ALL operations**, not overridden per operation
- [ ] `_correlationId` query parameter — **required on every call**, including GET
- [ ] `X-HNB.originatingChannel` and `X-HNB.requestingChannel` headers
- [ ] `Auth_Bearer` (OAuth2 token)
- [ ] `x-hnb.scopes` at info level = union of all operation scopes
- [ ] `x-hnb.scopes` per operation = only what that operation needs
- [ ] Every operation has at least a `200` and a `default`
- [ ] `/summary` limiter — "ideally, all APIs have one"; must be a strict subset of `_RESOURCE` **in the same structure**
- [ ] `_RESOURCE` **ends** with `_metadata: $ref __common_metadata_included`
- [ ] All collection schemas prefixed `<lower-back-bone-collection>_`
- [ ] `operationId` = `<Method><CollectionName><Limiter><Set>`, plural for collection ops, singular for resource ops
- [ ] Tags: plural for collection, singular for resource, `(set)` for multi-resource
- [ ] Unused `servers:` entries removed (internal-only API does not need the external/Fintech URLs)
- [ ] Validates in the SmartBear Swagger Editor
- [ ] **API Deployment Summary record created** + API Security Attestation checked

### Schema hierarchy — must be reproduced exactly

```
HTTP_200                    →  Response                       →  <collection>_base
HTTP_200_summary            →  Response_summary               →  <collection>_base_summary
HTTP_200_collection         →  Response_collection            →  <collection>_base
HTTP_200_collection_summary →  Response_collection_summary    →  <collection>_base_summary
HTTP_200_EXPANDEDRESOURCE   →  Response_EXPANDEDRESOURCE      →  <collection>_base_EXPANDEDRESOURCE

<collection>_base*  →  <collection>_RESOURCE | _SUMMARY | _EXPANDEDRESOURCE
```

---

# Part 3 — Your board maps cleanly onto the template

The sticky-note grid (six CMDB tables × *single record* / *all records* /
*filtered list*) is already the Heartbeats path pattern:

| Board sticky | Path | operationId |
|---|---|---|
| single record | `GET /<collection>/{<collection>Id}` | `get<Collection>` (singular) |
| all records | `GET /<collection>` | `get<Collection>s` (plural) |
| filtered list | `GET /<collection>?field=value` | same operation, query parameters |
| *(not on board, worth adding)* | `GET /<collection>/summary` | `get<Collection>sSummary` |
| *(bulk lookup by many ids)* | `POST /<collection>/retrieve` | `retrieve<Collection>s` |

**"Filtered list" is not a separate path.** It is the collection GET with query
parameters — and the standard requires every query parameter to be a field that
exists in `_RESOURCE` or the metadata.

That last rule is worth noting now: **you cannot filter on a field you have not
exposed in the resource.** So the field list and the filter list are the same
decision, made once.

`POST /retrieve` is worth considering for your use case — it converts a POST
into a GET when the query is too large or too sensitive for a URL. Querying
several hundred asset ids at once would exceed URL length limits.

---

# Part 4 — What I need from you

## Blocking — cannot write the contract without these

1. **Approved collection name(s) and abbreviations** from API Governance /
   Data Modeling. The standard says explicitly: *"it is best to confirm the
   collection name using the API Development Guidance process before creating
   an OAS."* This is the single biggest blocker.
2. **Classification** — HNB, Orchestration, or App (see 1.3)
3. **One OAS or two** — servers and applications together or separately (1.1)
4. **The resource identifier** — is it CMDB `sys_id`? Is it a GUID? (1.2)
5. **Supporting Team Initials** — goes in the filename
6. **`x-hnb.cmdbCorrelationId`** and **`x-hnb.cmdbName`** for your team
7. **`x-hnb.ownerEmail`** and **`x-hnb.approverEmail`**
8. **OAuth2 scope names** — from the master list; likely `<abbrev>:read`

## Important — needed for a complete first draft

9. **Field list for servers.** Which columns of `cmdb_ci_server` are exposed?
   The board sticky says (38) — is that a field count?
10. **Field list for applications** — `cmdb_ci_business_app`, board says (6)
11. **What identifies an application** — correlation id, and is it unique?
12. **Read-only for v1?** I am assuming GET only — no POST/PUT/PATCH/DELETE
13. **Internal only?** If yes, we delete the external and Fintech `servers:` entries
14. **EQH onboarding, or direct SoR implementation?** Determines which
    `__common_*` query parameters apply
15. **Datalake** — same collection with a source field, or a separate concern?

## Worth deciding early, not blocking

16. **CMDB is not the source of truth** (your own red sticky). Does the response
    carry a data-quality or coverage indicator? Where does "not in CMDB" surface?
17. **Sensitivity review.** Asset inventory is a target list — hostnames, IPs,
    owners, and risk ratings in one response. Worth asking Cyber Architecture
    what may be exposed and to whom, given this can reach external gateways.
18. **The other four tables** — application services, app-to-server, exception
    requests, risk and security profile. Separate collections later, or
    aggregates inside these two?

---

# Part 5 — What I can do right now without answers

- Draft the **full field mapping** from `cmdb_ci_server` and
  `cmdb_ci_business_app` into compliant names, with Code/Description pairs and
  Indicator/Timestamp/Date suffixes applied — this is the bulk of the work and
  none of it depends on the naming decisions
- Build a **skeleton OAS** with placeholder collection names, correct schema
  hierarchy, ping operations, security stanza, and the standard responses —
  then a find-and-replace applies the real names once Governance answers
- Write the **questions above as a one-page memo** you can take to Governance


---

# Addendum — 2026-08-17

## Q02 answered: HNB

Governance classifies this as **HNB**, not Orchestration. Consequences, all now
applied to the OAS:

- Filename prefix `HNB_`
- Module `hnb-<abbrev>`
- `info.title` begins with `HNB`
- **No `x-hnb.proxyPrefix`** — that is an Orchestration/App field

There is a second consequence worth putting in the charter rather than the
contract. Orchestration would have meant "we pass data through from CMDB." HNB
means Huntington expects this service to be a **system of reference in its own
right** — curating and reconciling, not proxying. That is a larger commitment
than it sounds, and it is the justification for the `dataQuality` aggregate:
if we are the reference, we owe callers a way to know where each answer came
from and when it was last true.

## The reference template does not parse

Found while wiring the validator into CI. This is verified, not suspected:

```
$ python3 -c "import yaml; yaml.safe_load(open('HNB_ExampleHeartbeats_3.1_20250319AGW.yaml'))"
found character '\t' that cannot start any token
  in "...", line 2085, column 9
```

| Defect | Lines affected | Rejected by |
|---|---|---|
| Tab characters in indentation | 140 | **every YAML parser** |
| `key:{` with no space after the colon | 35 | `openapi-spec-validator` |
| Flow collection wrapped to a continuation line at the parent's indent | 12 | **js-yaml — what Swagger Editor runs** |
| CRLF line endings | 2,840 | nothing, but it will fight `.gitattributes` |

The tabs come from JSON example blocks pasted in with their original
indentation. Anyone who copies an example block out of that template inherits
them, and the file stops loading.

**Why this is the interesting finding, not just a typo.** PyYAML accepts two of
the three defects. So the failure mode is: the file loads on your laptop, the
diff looks fine, review passes, and it breaks the first time a Governance
reviewer pastes it into Swagger Editor — the single most expensive moment for
it to break. That is the same shape as every other bad failure we have hit on
this project: **not an error, a silent wrong answer that surfaces late.**

Our OAS had inherited the flow-mapping style from the template. `servers[].variables`
is now block style, and `scripts/validate_oas.py` fails the build on all three
defects. Running it against the template is a useful demonstration: four
failures, in the file we were told to copy.

## What changed in the OAS

- `servers[].variables` rewritten in block style with an explanatory comment
- Q02 marker closed
- Q15 annotated: 38 source columns ≠ 38 API fields
- Now passes `openapi-spec-validator` as well as the governance validator
- 1,849 lines; 40 `[ANSWER-NEEDED]`, 29 `PLACEHOLDER`
