# Cyber Inventory API — Question Sheet

Every open decision in `HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml`, numbered.
Each `Qnn` here matches an inline `[ANSWER-NEEDED Qnn]` tag in the OAS.

```bash
# find every open item in the OAS
grep -n "ANSWER-NEEDED" HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml

# find the ones for a specific question
grep -n "ANSWER-NEEDED Q18" HNB_Cyber-inventories-servers_1.0_PLACEHOLDER.yaml
```

**Nothing gets submitted to Governance until that first grep returns zero.**

---

## How to use this sheet

Questions are grouped by **who answers them**, because that determines how long
they take. The Governance ones have lead time measured in days; the team ones can
be settled in a room this afternoon.

| Group | Who | Count | Blocking? |
|---|---|---|---|
| A | API Governance / Data Modeling | 4 | **Yes — cannot write the contract** |
| B | Your team / product owner | 8 | Yes for a complete draft |
| C | CMDB / data owners | 4 | Yes for a complete draft |
| D | Cyber Architecture / Security | 2 | Before production, raise now |
| E | Platform / deployment | 2 | Before submission, not before drafting |

---

# Group A — API Governance / Data Modeling

*These four change the filename, module name, title, scopes, and every schema
prefix in the document. Ask first; everything else is cheaper to change later.*

### Q01 — What is the approved collection name, and its abbreviation?

**Why it blocks everything:** the collection name determines the filename, the
module name, the title, the OAuth2 scopes, the path, the resource id, and the
prefix on all 96 schemas. The standard says to confirm it through the API
Development Guidance process *before* creating an OAS.

Placeholder in use: `cyber-inventories-servers` / abbreviation `cy-inv-srvr`.

It is well-formed against the naming rules (right-most token plural, second level
plural, first level singular when there is more than one level) but it is **not
approved**. Governance assigns abbreviations.

- [ ] Approved collection name (servers): ______________________
- [ ] Approved abbreviation: ______________________
- [ ] Approved collection name (applications): ______________________
- [ ] Approved abbreviation: ______________________

**Also ask:** does the Enterprise Information Model already have a home for
infrastructure/asset concepts that we should be extending rather than creating?

---

### Q02 — Classification: HNB, Orchestration, or Application?

**Our reading:** this is an **Orchestration/Composite API**. The standard defines
one as spanning multiple domains and *"typically DOES NOT have its own data store
and instead is orchestrating across other domains that DO have a data store."*
This service reads from the CMDB (ServiceNow is the SoR) and later a datalake, and
owns no authoritative data.

**Counter-argument to put to them:** if the cyber inventory is intended to become
a system of *reference* in its own right — curating, enriching, and reconciling
data rather than passing it through — HNB may be correct.

| If | Filename | Module | Title | `proxyPrefix` |
|---|---|---|---|---|
| HNB | `HNB_<Collection>_<Ver> <CCYYMMDD>-<Init>.yaml` | `hnb-<abbrev>` | `Huntington <Collection> API` | `HNB` |
| Orch | `Orch_<Collection>_<Ver> <CCYYMMDD>-<Init>.yaml` | `orch-<abbrev>` | `Orchestration / Composite <Collection> API` | *confirm* |
| App | `App_<AppName>-<Collection>_<Ver> …` | `app-<appname>-<abbrev>` | `Application <Abbrev> <Collection> API` | `App` |

- [ ] Classification: ______________________
- [ ] If Orchestration, what is the correct `x-hnb.proxyPrefix` value? ____________

---

### Q03 — What is the resource identifier, and is it a GUID?

**The conflict, stated plainly.** The plan was `GET /servers/{assetId}`. The
standard forbids it:

> **Correct:** `GET /customer-relationships-accounts?accountId=98765`
> **Incorrect:** `GET /customer-relationships-accounts/{accountId}`

Only the collection's own resource id may be a path parameter, and that id is
derived mechanically: singular collection name + `Id`. There is a second rule
stacked on top:

> In nearly all cases, the unique identifier should be a GUID so as to ensure
> opaqueness AND provide a security defense against an attack vector of a small
> namespace.

CMDB `sys_id` is a 32-character GUID and satisfies both rules for free.

**Recommendation:** `sys_id` becomes `cyberInventoriesServerId` (path);
`assetId` becomes a query filter. Callers holding an asset id do one query
instead of one path lookup — functionally identical, standards-clean.

- [ ] Resource id maps to: ______________________
- [ ] Is it a GUID? ☐ yes ☐ no — if no, an approved exception is required
- [ ] Is `assetId` globally unique? *(if not, a lookup may legitimately return more than one server)*
- [ ] Same question for applications: is `correlationId` the resource id, or a filter?

---

### Q13 — Which Heartbeats version is current, and has the common section been copied verbatim?

The standard says of the common components block: *"AVOID changing (i.e. DO NOT
change) anything from here to 'common components and responses END'."*

The `__common_*` schemas in our file are structurally faithful and let it validate
standalone, but they are **hand-written**. Before submission they must be replaced
with a verbatim copy from the current template. Hand-maintained copies drift, and
drift in the common section breaks the onboarding automation.

- [ ] Current Heartbeats version at build time: ______________________
- [ ] Common section replaced verbatim? ☐

---

# Group B — Your team / product owner

### Q09 — Confirmed: GET only?

**Answered — yes, GET only.** Recorded here for the reviewer's benefit.

Consequences already applied: `x-hnb.idempotency: 'Disabled'`, no POST/PUT/PATCH/
DELETE operations, no `(set)` tag, no request-body schemas except `/retrieve`.

**One nuance to resolve — see Q12.**

---

### Q12 — Does "GET only" permit the `/retrieve` POST-as-GET pattern?

The standard blesses `POST /<collection>/retrieve` as a **read** operation:

> NOTE that "/retrieve" is not actually a limiter but instead a special notation
> that converts a POST (with sensitive data in the payload) to a GET operation.

It exists because a caller reconciling the fleet will look up several hundred
asset ids at once, which exceeds practical URL length limits on a GET.

It uses the POST **verb** even though it performs no mutation.

- [ ] Is bulk lookup required for v1? ☐ yes ☐ no
- [ ] If "GET only" is literal (verb-level), delete both `/retrieve` paths ☐

---

### Q11 — Internal only?

**Strong recommendation: yes.** Delete the External (Colleague/Partner) and
External (Customer/Fintech) server entries.

A fleet-wide list of hostnames, IP addresses, OS versions, internet-facing flags,
open vulnerability counts, and risk ratings is a **target list**. It should not be
reachable from an external gateway.

- [ ] Internal only? ☐ yes ☐ no
- [ ] If no, justify at Cyber Architecture Review

---

### Q14 — Do string filters support partial matching, or exact only?

Affects `serverName`, `applicationName`, `supportGroupName`. "Show me every server
whose name starts with `web-prd`" is a very likely first request.

- [ ] Exact match only ☐  Contains ☐  Starts-with ☐
- [ ] If partial matching, is it expressed via the `operator` field in `/retrieve`,
      or via a separate query parameter convention?

---

### Q15 — What is the confirmed field set?

Your board sticky reads `cmdb_ci_server` **(38)**. If that is a field count, the
current `_RESOURCE` is short.

Every candidate CMDB column needs an individual decision:
**expose / omit / rename / split into Code + Description.**

- [ ] Is (38) a field count, a table id, or something else? ______________________
- [ ] Same for `cmdb_ci_business_app` **(6)** ______________________
- [ ] Confirmed server field list attached? ☐
- [ ] Confirmed application field list attached? ☐

**Reminder that makes this one decision, not two:** every query parameter must be
a field that exists in `_RESOURCE`. **You cannot filter on a field you have not
exposed.** So the field list and the filter list are settled together.

---

### Q17 — Should `expand_resources` inline the full application resource?

Today `ownership.applicationCorrelationReference` returns an identifier. With
`expand_resources=true`, should the response inline the whole application object?

If yes, the standard requires copying the applications collection `_RESOURCE`
schema into this document — *"all of the referenced schemas from the referenced
API must be copied into this API (place them at the bottom)"* — and not
reorganising or overriding the other collection's definitions.

- [ ] Inline expansion supported in v1? ☐ yes ☐ no

---

### Q16 — How does "not in the CMDB" surface in the response?

This comes straight off your red stickies: *"CMDB is NOT source of truth for
everything"*, *"how to find what's NOT in CMDB"*, *"MOCK anything external to CMDB"*.

The `dataQuality` aggregate exists for this. Without it the API reports "we have no
record" and "the attribute is genuinely empty" **identically** — which is the same
silent wrong-answer failure mode as reporting a proxy's certificate as a host's.

- [ ] Does v1 surface servers observed *outside* the CMDB? ☐ yes ☐ no
- [ ] If yes, what populates `authoritativeSourceName`? ______________________
- [ ] Is a separate coverage/gap endpoint needed, or does `cmdbRecordFoundIndicator` suffice?

---

### Q10 — What are the expected call volumes?

The quota values in the file are **copied from the Heartbeats example and are
almost certainly wrong**. A nightly coverage report pulling the whole fleet could
exceed the Gold tier in a single run.

- [ ] Expected peak calls/minute, non-production: ____________
- [ ] Expected peak calls/minute, production: ____________
- [ ] Is there a bulk/batch consumer (reporting, datalake sync) with a different profile?

---

### Q20 — Is `serialNumber` an acceptable field name?

The standard forbids `number` as a **standalone** field name. `serialNumber` is a
compound and should be fine, but it is worth a one-line confirmation rather than a
review finding.

- [ ] Confirmed with Governance ☐  Alternative name if not: ______________________

---

# Group C — CMDB / data owners

### Q18 — What are the real enumerated values? *(8 places in the OAS)*

Every `*Code` field currently carries an **assumed** enum. Each needs confirming
against the actual CMDB column, and each needs its matching `*Description`.

| Field | Assumed values | Confirmed? |
|---|---|---|
| `environmentCode` | production, disasterRecovery, staging, test, development, unknown | ☐ |
| `operationalStatusCode` | operational, nonOperational, repairInProgress, retired, unknown | ☐ |
| `installStatusCode` | installed, inStock, onOrder, inMaintenance, pendingInstall, pendingRepair, retired, absent, unknown | ☐ |
| `lifecycleStageCode` | planned, build, active, maintenance, endOfLife, decommissioned, unknown | ☐ |
| `riskRatingCode` | critical, high, moderate, low, notAssessed | ☐ |
| `dataClassificationCode` | public, internal, confidential, restricted, notClassified | ☐ |
| `complianceScopeCode` | pci, sox, glba, ffiec, none, multiple | ☐ |
| `patchCurrencyCode` | current, oneCycleBehind, twoCyclesBehind, moreThanTwoCyclesBehind, unknown | ☐ |

**Note on `complianceScopeCode`:** a server can plausibly be in scope for more
than one regime. If so this needs to be an **array**, not a single code — a
`multiple` value that hides which regimes apply is not useful to a consumer.

- [ ] Can a server have multiple compliance scopes? ☐ yes ☐ no

**Note on renamed columns.** CMDB uses `operational_status` and `install_status`.
`status` is a **forbidden standalone field name** under the standard, so both were
renamed and paired with a Description. Confirm the mapping is faithful.

---

### Q07 — EQH-onboarded, or direct to the SoR?

Determines which `__common_*` query parameters are real. The Heartbeats set assumes
the EQH answers GETs; a direct Fuse/GCP implementation supports a subset.

- [ ] `x-hnb.target.default`: ☐ EQH ☐ GCP ☐ OCP ☐ other: __________
- [ ] If not EQH, which of these are actually supported?
      `field_list` ☐ `sort_by` ☐ `count_only` ☐ `include_total_results` ☐
      `expand_resources` ☐ `include_metadata` ☐

**Do not document a parameter the implementation ignores.** A query parameter that
silently does nothing is worse than an absent one — the caller believes they
filtered.

---

### Q19 — Sensitivity: may IP addresses and personal names be returned?

Two fields need a decision from Cyber Architecture, not from us:

- **`infrastructure.ipAddress`** — combined with hostname, OS version,
  `internetFacingIndicator`, and open vulnerability counts, a response is a
  ready-made reconnaissance package.
- **`ownership.ownedByName` / `managedByName`** — personal names are PII. A group
  or role reference may serve the purpose without the exposure.

The standard's `accountId`-versus-`accountNumber` guidance is the precedent: expose
the identifier, not the sensitive value, and make consumers who genuinely need the
sensitive value go to the owning system for it.

- [ ] `ipAddress` exposed? ☐ yes ☐ no ☐ only to specific scopes
- [ ] Personal names exposed, or replaced with group/role? ______________________
- [ ] Does the response need a `classificationHighwatermark` floor?

---

### Q06 — What are the approved OAuth2 scope names?

Placeholder: `cy-inv-srvr:read`. Confirm against the Governance master scope list
(see the FAQ: *"What is/are the OAuth2 scope(s) for my API?"*).

- [ ] Scope for read operations: ______________________
- [ ] Is a separate scope needed for the risk/vulnerability aggregates, so that a
      general consumer can read inventory without reading security posture?

*That last one is worth thinking about. Inventory and vulnerability data have very
different audiences.*

---

# Group D — Cyber Architecture / Security

Covered inside Q19 and Q11. Raise both at the Cyber Architecture Review, which the
Deployment Summary's API Security Attestation requires you to have completed:

> I have read, understood and will implement applicable Huntington API Security
> requirements per the API Security Standard (ITRC-2105) to address applicable
> OWASP API Top 10 risks for my API, before deploying to Production. My Project has
> gone through the Cyber Architecture Review process and outcomes were fulfilled.

---

# Group E — Platform / deployment

### Q04 — Team CMDB correlation id and name

- [ ] `x-hnb.cmdbCorrelationId`: ______________________
- [ ] `x-hnb.cmdbName`: ______________________

### Q05 — Contact details *(5 places in the OAS)*

- [ ] `info.contact.name` (owning IT team): ______________________
- [ ] `info.contact.url` (documentation site): ______________________
- [ ] `info.contact.email`: ______________________
- [ ] `x-hnb.ownerEmail`: ______________________
- [ ] `x-hnb.approverEmail`: ______________________
- [ ] **Supporting Team Initials** for the filename: ______________________

### Q08 — Deployment endpoints per environment

Not known until the service is deployed. Placeholders must be replaced before
submission.

- [ ] dv / in / qa / st / tr / pd audience + endpoint URLs collected ☐

---

# Summary — the four that block writing

| # | Question | Owner |
|---|---|---|
| **Q01** | Approved collection name + abbreviation | API Governance |
| **Q02** | Classification: HNB / Orch / App | API Governance |
| **Q03** | Resource identifier — `sys_id`, and is it a GUID? | API Governance |
| **Q13** | Common section copied verbatim from current Heartbeats | API Governance |

Everything else can be drafted around. **These four cannot.**
