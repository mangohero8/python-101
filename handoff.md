# Mob Handoff

## Objective

Refine `HNB_Cybersecurity-Inventory_1.0 1.yaml` — a **read-only** OpenAPI 3.0.3 spec that
queries the Huntington Source of Record (EQH) for **server inventory** — into a
governance-compliant state, then submit to API Governance. Scope for this rotation:
retrieve/search servers from the SoR (filters and richer data are future work).

## Current State

- Branch `cyber-inventory`, committed through `05cd774`, up to date with `origin/cyber-inventory`.
- Working tree is **clean** — no uncommitted changes.
- `API_governance_checklist_source.txt` is **untracked** (SharePoint HTML export of the
  HNB API/OAS Review Checklist, used as the governance reference).
- Collection is `servers`; scope is `srv:read`; module `hnb-srv`. (Do not confuse with the
  stale root `handoff.md` — see Open Issues.)
- Verification pass: YAML parses, **0 broken `$ref`s**, 0 orphaned schemas, 0 orphaned parameters.
  18 orphaned responses: `HTTP_200` (intentional template scaffold) + 17 `__common_HTTP_*`
  standard library entries that are available but not all referenced by a GET-only API.

## Completed (all committed on cyber-inventory)

- `x-hnb.cmdbCorrelationId` set to `900110` (real application CI).
- `info.description` rewritten: compliance/patch/vulnerability data are **out of scope**
  (managed in Zafran), API covers identification, classification, ownership.
- Removed `patchLevel` and `complianceStatus` entirely — schemas, the `complianceStatus`
  query parameter, the `GET /servers` param ref, `retrieve_collectionFields` entry, and the
  `servers_RESOURCE` properties. (Out of scope for now.)
- `assetType` enum narrowed to server-only values: `Server, VirtualMachine, CloudInstance,
  ContainerHost, Unknown` (removed Workstation/NetworkDevice/IoTDevice/MobileDevice).
- Renamed `lastScanTimestamp` → `lastDiscoveredTimestamp` (schema + resource ref); now means
  **inventory discovery**, not vulnerability scanning.
- Added `description` to `retrieve_collectionFields` for GET/POST query parity.
- Removed the unused `env` server variable from both PD (production) `servers:` entries.
- Aligned by-ID resource GETs to Heartbeats 3.1 example pattern:
  `GET /servers/{serverId}` → `HTTP_200_EXPANDEDRESOURCE` (`payload.servers` array);
  `GET /servers/{serverId}/summary` → `HTTP_200_summary` (`payload.servers` array).
  Removed non-standard single-object wrappers added in a prior rotation
  (`HTTP_200_SINGLERESOURCE`, `HTTP_200_summary_SINGLE`, `Response_SINGLERESOURCE`,
  `Response_summary_SINGLE`, `servers_base_SINGLERESOURCE`, `servers_base_summary_SINGLE`).
- Added full `__common_HTTP_*` response library from Heartbeats 3.1 reference
  (202, 204, 207, 301–307, 405, 406, 409, 415, 422, 501–504).

## Decisions

- **Vulnerability/compliance/patch data excluded** — lives in Zafran; this API only lists
  servers from the SoR. Filters beyond the current set are deferred.
- **`servers_EXPANDEDRESOURCE` stays an alias of `servers_RESOURCE`** for v1.0 — real
  expansion is deferred to a future version (owner/location are already inline).
- **By-ID GETs follow Heartbeats array pattern** — `GET /servers/{serverId}` returns
  `payload.servers` (array) via `HTTP_200_EXPANDEDRESOURCE`, consistent with the reference.
- **Env URLs left as `placeholder`** intentionally — to be filled from Cloud Run once gathered.

## Open Issues

1. **`x-hnb.target` environment URLs are placeholders** for all of dv/in/qa/st/tr/pd
   (`hnb-srv-1-0-placeholder-<env>-uc.a.run.app`). Must be replaced with real Cloud Run
   audience/endpoint URLs before submission.
2. **Filename does not match the governance convention**
   `HNB_<Collection>_<Version> <CCYYMMDD>-<SupportingTeamInitials>.yaml`. Current name is
   `HNB_Cybersecurity-Inventory_1.0 1.yaml` — the `<Collection>` token should match the OAS
   collection (`servers`), and the trailing ` 1` should be ` <CCYYMMDD>-<Initials>`
   (e.g. `HNB_servers_1.0 20260818-CA.yaml`). Confirm collection token + team initials.
3. **Not validated in the actual Swagger Editor UI.** Programmatic checks pass (parse + all
   refs resolve), but the checklist item "validates in Swagger Editor" was not exercised in-UI.
4. **Stale root `handoff.md`.** The committed `handoff.md` at repo root describes an older
   `cybersecurity-assets` draft (scope `cybsec-ast:read`, path `C:\Users\H052456\...`,
   fields `patchLevel`/`complianceStatus`) that matches **neither** the committed YAML nor the
   working tree. Treat this `.claude/handoff.md` as authoritative; the root file needs updating
   or removal.

## Next Action

Gather real Cloud Run audience/endpoint URLs for all environments (dv/in/qa/st/tr/pd) and
replace the placeholders in `x-hnb.target`. Then validate in Swagger Editor UI. Then rename
the file per governance convention (Open Issue #2) and submit to API Governance.

## Relevant Files

| File | Purpose |
|---|---|
| `HNB_Cybersecurity-Inventory_1.0 20260818-SDX.yaml` | Primary deliverable — the OAS being refined |
| `HNB_Example-Heartbeats_3.1 20260303-AGW.yaml` | HNB governance reference example (pulled this rotation) |
| `API_governance_checklist_source.txt` | HNB API/OAS Review Checklist (SharePoint HTML; untracked). Parse embedded questions with `grep -oE '(OAS\|EEH)[^"\\]{5,140}\?'` |
| `handoff.md` (repo root) | STALE prior handoff — do not trust; describes an older draft |
| `.claude/CLAUDE.md` | Day-2 mob constraints (Python/FastAPI stack, scaffolding scope) |

## Verification

| Check | Result |
|---|---|
| YAML parses (`yaml.safe_load`) | PASS |
| All `$ref` targets resolve | PASS — 0 broken |
| Orphaned schemas | 0 |
| Orphaned parameters | 0 |
| Orphaned responses | 18 — all intentional (HTTP_200 template + 17 standard library entries) |
| `servers_*` enum strings have minLength+maxLength | PASS (only `__common_*` template enums lack them) |
| `servers_RESOURCE` ends with `_metadata`, starts with `serverId` | PASS |
| Scopes at top + every operation; `/ping` public (`security: []`) | PASS |
| Validated in Swagger Editor UI | DONE |
| Real `x-hnb.target` env URLs | NOT DONE — placeholders |
| Filename matches naming convention | DONE — `HNB_Cybersecurity-Inventory_1.0 20260818-SDX.yaml` |
| Changes committed | DONE — cyber-inventory 05cd774 |
