#!/usr/bin/env python3
"""Validate an OAS against the Huntington API/OAS Review Checklist.

    python3 scripts/validate_oas.py <file.yaml> [--strict]

Exit codes:
    0  all enforced rules pass
    1  one or more rules FAILED
    2  --strict and there are unresolved [ANSWER-NEEDED] / PLACEHOLDER markers

WHY THIS EXISTS

The governance rules are currently enforced by a human reading a checklist at
submission time. That is the most expensive possible moment to find a finding -
the OAS has already been written, reviewed internally, and scheduled.

Every rule below is mechanically checkable. Running them on every commit turns
"we hope this complies" into "the pipeline will not let it not comply", which is
the Continuous Compliance idea applied to a contract rather than to code.

WHAT THIS DOES NOT DO

It cannot check judgement: whether the collection name is right, whether a field
should be exposed, whether an enum matches reality. Those still need Governance
and a human. This catches the mechanical findings so the human review is spent on
the decisions that actually need a person.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("FATAL: pyyaml is required.  pip install pyyaml", file=sys.stderr)
    sys.exit(1)

FORBIDDEN_STANDALONE = {"status", "statuses", "number", "distance", "amount"}
FORBIDDEN_SUFFIXES = ("id", "Identifier", "identifier")

RESULTS: list[tuple[str, str, str]] = []   # (level, rule, detail)


def ok(rule: str, detail: str = "") -> None:
    RESULTS.append(("PASS", rule, detail))


def fail(rule: str, detail: str) -> None:
    RESULTS.append(("FAIL", rule, detail))


def warn(rule: str, detail: str) -> None:
    RESULTS.append(("WARN", rule, detail))


# --------------------------------------------------------------------------
def check_parses(path: Path):
    try:
        doc = yaml.safe_load(path.read_text())
        ok("OAS parses as YAML")
        return doc
    except yaml.YAMLError as exc:
        fail("OAS parses as YAML", str(exc).split("\n")[0])
        return None


def check_openapi_version(d):
    v = d.get("openapi")
    (ok if v == "3.0.3" else fail)("openapi version is 3.0.3", f"found {v!r}")


def check_refs_resolve(d, text):
    refs = set(re.findall(r'\$ref:\s*"#/components/(\w+)/([^"]+)"', text))
    comp = d.get("components", {})
    bad = [f"{s}/{n}" for s, n in refs if n not in (comp.get(s) or {})]
    (ok if not bad else fail)(
        f"all {len(refs)} internal $refs resolve", ", ".join(bad[:5])
    )


def check_single_collection(d):
    """One OAS = one Collection. Detect a second root collection in the paths."""
    roots = set()
    for p in d.get("paths", {}):
        seg = p.strip("/").split("/")[0]
        if seg and not seg.startswith("{") and seg != "ping":
            roots.add(seg)
    (ok if len(roots) <= 1 else fail)(
        "exactly one root collection", f"found {sorted(roots)}"
    )
    return next(iter(roots), None)


def check_collection_naming(collection):
    """Right-most plural, second-level plural, first level singular when >1 node."""
    if not collection:
        return
    nodes = collection.split("-")
    problems = []
    if not nodes[-1].endswith("s"):
        problems.append(f"right-most node {nodes[-1]!r} should be plural")
    if len(nodes) > 1 and not nodes[-2].endswith("s"):
        problems.append(f"second-level node {nodes[-2]!r} should be plural")
    if len(nodes) > 1 and nodes[0].endswith("s"):
        problems.append(f"first node {nodes[0]!r} should be singular when there is >1 node")
    if collection != collection.lower():
        problems.append("collection must be lower-back-bone-case")
    (ok if not problems else fail)("collection naming rules", "; ".join(problems))


def check_path_parameters(d, collection):
    """THE most commonly broken rule: only the resource id may be a path parameter."""
    if not collection:
        return
    singular = collection[:-1] if collection.endswith("s") else collection
    expected = "".join(
        w.capitalize() if i else w for i, w in enumerate(singular.split("-"))
    ) + "Id"
    used = set(re.findall(r"\{([^}]+)\}", " ".join(d.get("paths", {}))))
    bad = used - {expected}
    if bad:
        fail(
            "only the resource id is a path parameter",
            f"illegal path params {sorted(bad)} - expected only {expected!r}. "
            f"Move them to query parameters.",
        )
    else:
        ok("only the resource id is a path parameter", f"{expected}")
    return expected


def check_numeric_keywords(schemas):
    bad = [
        n for n, s in schemas.items()
        if isinstance(s, dict) and s.get("type") in ("integer", "number")
        and ({"minLength", "maxLength"} & set(s))
    ]
    (ok if not bad else fail)(
        "numeric fields use minimum/maximum only", ", ".join(bad[:5])
    )


def check_enum_keywords(schemas):
    bad = [
        n for n, s in schemas.items()
        if isinstance(s, dict) and "enum" in s
        and ({"minLength", "maxLength"} & set(s))
    ]
    (ok if not bad else fail)(
        "enum strings carry no minLength/maxLength", ", ".join(bad[:5])
    )


def check_code_description_pairs(schemas):
    names = set(schemas)
    bad = [n for n in names if n.endswith("Code") and n[:-4] + "Description" not in names]
    (ok if not bad else fail)(
        "every *Code has a matching *Description", ", ".join(bad[:5])
    )


def _walk_properties(node, path=""):
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict):
            for name in props:
                yield name, path
        for k, v in node.items():
            yield from _walk_properties(v, f"{path}/{k}")
    elif isinstance(node, list):
        for item in node:
            yield from _walk_properties(item, path)


def check_forbidden_names(d):
    bad, suffix_bad = [], []
    for name, where in _walk_properties(d):
        if name in FORBIDDEN_STANDALONE and "__common" not in where:
            bad.append(f"{name} (at {where})")
        if name.endswith(FORBIDDEN_SUFFIXES) and not name.endswith("Id"):
            suffix_bad.append(name)
    (ok if not bad else fail)(
        "no forbidden standalone field names", ", ".join(sorted(set(bad))[:5])
    )
    (ok if not suffix_bad else fail)(
        "no forbidden id/Identifier suffixes", ", ".join(sorted(set(suffix_bad))[:5])
    )


def check_resource_ends_with_metadata(schemas, collection):
    key = f"{collection}_RESOURCE"
    res = schemas.get(key)
    if not res:
        fail("_RESOURCE exists", f"{key} not found")
        return
    props = list(res.get("properties", {}))
    if not props:
        fail("_RESOURCE has properties", key)
    elif props[-1] != "_metadata":
        fail("_RESOURCE ends with _metadata", f"ends with {props[-1]!r}")
    else:
        ok("_RESOURCE ends with _metadata")


def check_summary_is_subset(schemas, collection):
    res = schemas.get(f"{collection}_RESOURCE", {}).get("properties", {})
    summ = schemas.get(f"{collection}_SUMMARY", {}).get("properties", {})
    if not summ:
        warn("_SUMMARY exists", "no _SUMMARY limiter - the standard says every API should have one")
        return
    extra = set(summ) - set(res)
    (ok if not extra else fail)(
        "_SUMMARY is a strict subset of _RESOURCE", f"extra fields {sorted(extra)}"
    )


def check_ping_scopes(d):
    paths = d.get("paths", {})
    proxy = paths.get("/ping", {}).get("get", {}).get("x-hnb.scopes")
    if proxy is None:
        fail("/ping operation exists", "missing")
    elif proxy != [""]:
        fail("/ping scope is [\"\"]", f"found {proxy!r} - the standard says DO NOT MODIFY")
    else:
        ok("/ping scope is [\"\"]")

    coll_ping = [p for p in paths if p.endswith("/ping") and p != "/ping"]
    if not coll_ping:
        fail("/<collection>/ping operation exists", "missing")
    else:
        sc = paths[coll_ping[0]].get("get", {}).get("x-hnb.scopes") or []
        (ok if any(s.endswith(":read") for s in sc) else fail)(
            "/<collection>/ping uses the :read scope", f"found {sc!r}"
        )


def check_responses(d):
    bad = []
    for p, ops in d.get("paths", {}).items():
        for m, op in ops.items():
            if not isinstance(op, dict):
                continue
            r = set(op.get("responses", {}))
            missing = {"200", "default"} - r
            if missing:
                bad.append(f"{m.upper()} {p} missing {sorted(missing)}")
    (ok if not bad else fail)(
        "every operation has 200 and default", "; ".join(bad[:5])
    )


def check_security_not_overridden(d):
    if "security" not in d:
        fail("global security stanza present", "missing")
    else:
        ok("global security stanza present")
    per_op = [
        f"{m.upper()} {p}"
        for p, ops in d.get("paths", {}).items()
        for m, op in ops.items()
        if isinstance(op, dict) and "security" in op
    ]
    (ok if not per_op else fail)(
        "security not overridden per operation",
        f"{per_op[:5]} - the standard says use the default for ALL operations",
    )


def check_operation_ids(d, collection):
    """Plural collection name when the resource id is NOT a path param, singular when it is."""
    if not collection:
        return
    bad = []
    for p, ops in d.get("paths", {}).items():
        has_path_param = "{" in p
        for m, op in ops.items():
            if not isinstance(op, dict):
                continue
            oid = op.get("operationId")
            if not oid:
                bad.append(f"{m.upper()} {p} has no operationId")
                continue
            if p.endswith("/ping"):
                continue
            core = "".join(w.capitalize() for w in collection.split("-"))
            singular = core[:-1] if core.endswith("s") else core
            if has_path_param and core in oid:
                bad.append(f"{oid} should use the SINGULAR collection name")
            elif not has_path_param and core not in oid and singular in oid:
                bad.append(f"{oid} should use the PLURAL collection name")
    (ok if not bad else fail)("operationId naming convention", "; ".join(bad[:5]))


def check_scopes_declared(d):
    top = set(d.get("info", {}).get("x-hnb.scopes") or [])
    used = set()
    for ops in d.get("paths", {}).values():
        for op in ops.values():
            if isinstance(op, dict):
                used |= {s for s in (op.get("x-hnb.scopes") or []) if s}
    missing = used - top
    (ok if not missing else fail)(
        "info.x-hnb.scopes is the union of all operation scopes",
        f"used but not declared: {sorted(missing)}",
    )


def check_query_params_are_resource_fields(d, collection):
    """Every query parameter must be a field in _RESOURCE or metadata."""
    schemas = d.get("components", {}).get("schemas", {})
    res = schemas.get(f"{collection}_RESOURCE", {}).get("properties", {})
    known = set(res)
    for agg in res:
        sub = schemas.get(f"{collection}_{agg}", {}).get("properties", {})
        known |= set(sub)
    unknown = []
    for name, param in (d.get("components", {}).get("parameters") or {}).items():
        if param.get("in") != "query":
            continue
        pname = param.get("name", "")
        if pname.startswith(("show_", "_")) or name.startswith("__common"):
            continue
        base = re.sub(r"_(min|max)$", "", pname)
        if base not in known:
            unknown.append(pname)
    (ok if not unknown else fail)(
        "every query parameter exists in _RESOURCE",
        f"{unknown[:5]} - you cannot filter on a field you have not exposed",
    )


def check_open_markers(text):
    a = len(re.findall(r"ANSWER-NEEDED", text))
    p = len(re.findall(r"PLACEHOLDER", text))
    return a, p


# --------------------------------------------------------------------------
def check_yaml_portability(text: str) -> None:
    """Reject YAML that PyYAML accepts but stricter parsers do not.

    THIS RULE EXISTS BECAUSE THE REFERENCE TEMPLATE FAILS IT.

    The template writes server variables as flow mappings, and does two things
    that are legal only by PyYAML's leniency:

      1. a key, a colon, and an opening brace with no space between the colon
         and the brace. YAML only treats a colon as a key separator in flow
         context when a space follows it (or the key is quoted), so a strict
         parser reads the whole thing as one plain scalar and then chokes on
         the brace. openapi-spec-validator rejects it.

      2. a flow collection wrapped across lines with the continuation indented
         to the same column as its parent key. js-yaml - the YAML parser
         Swagger Editor runs on - rejects that as "deficient indentation".

    Neither is visible from Python, which is the whole problem: the file parses
    locally, gets committed, and fails at the one moment it must not - when a
    reviewer pastes it into Swagger Editor. This check moves that failure to
    the commit that caused it.
    """
    lines = text.splitlines()

    # 0. tab characters.
    #
    # YAML forbids tabs in indentation, full stop. The reference template we
    # were given contains 140 lines with tabs - JSON examples pasted in with
    # their original indentation - which means THAT FILE DOES NOT PARSE IN ANY
    # YAML PARSER. Copying an example block out of it brings the tabs along.
    tabs = [i + 1 for i, ln in enumerate(lines) if "\t" in ln]
    if tabs:
        fail("no tab characters", f"line(s) {tabs[:6]} - YAML forbids tabs in indentation")
    else:
        ok("no tab characters")

    # 1. colon immediately followed by an opening brace.
    tight = [i + 1 for i, ln in enumerate(lines)
             if not ln.lstrip().startswith("#") and re.search(r"[^\s]:\{", ln)]
    if tight:
        fail("flow mapping needs a space after ':'", f"line(s) {tight[:6]}")
    else:
        ok("flow mapping needs a space after ':'")

    # 2. flow collection left open at end of line.
    #
    # Braces appear legitimately inside quoted strings ("{module}/{version}"),
    # inside unquoted path keys (/servers/{serverId}:), and inside prose in
    # block scalars. We strip quoted spans, and skip block scalars entirely by
    # tracking the indentation of the line that opened one.
    open_flow: list[int] = []
    block_indent: int | None = None
    for i, raw in enumerate(lines):
        stripped = raw.strip()
        indent = len(raw) - len(raw.lstrip())

        if block_indent is not None:
            if stripped and indent <= block_indent:
                block_indent = None      # block scalar ended
            else:
                continue                 # still inside it - ignore

        if not stripped or stripped.startswith("#"):
            continue
        if re.search(r":\s*[|>][-+0-9]*\s*$", raw):
            block_indent = indent
            continue

        body = re.sub(r'"[^"]*"', '""', raw)
        body = re.sub(r"'[^']*'", "''", body)
        body = body.split(" #")[0]
        depth = body.count("{") - body.count("}") + body.count("[") - body.count("]")
        if depth > 0:
            open_flow.append(i + 1)

    if open_flow:
        fail("flow collections must close on one line", f"line(s) {open_flow[:6]}")
    else:
        ok("flow collections must close on one line")


# --------------------------------------------------------------------------
def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    path = Path(sys.argv[1])
    strict = "--strict" in sys.argv

    if not path.exists():
        print(f"FATAL: {path} not found", file=sys.stderr)
        return 1

    text = path.read_text()

    # Portability runs BEFORE the parse gate on purpose. A tab in the
    # indentation makes the file unparseable, and "OAS parses as YAML: FAIL"
    # on its own does not tell you why. Running the text-level checks first
    # means the output names the actual cause even when nothing else can run.
    check_yaml_portability(text)

    doc = check_parses(path)
    if doc is None:
        _report()
        return 1

    schemas = doc.get("components", {}).get("schemas", {}) or {}

    check_openapi_version(doc)
    check_refs_resolve(doc, text)
    collection = check_single_collection(doc)
    check_collection_naming(collection)
    check_path_parameters(doc, collection)
    check_numeric_keywords(schemas)
    check_enum_keywords(schemas)
    check_code_description_pairs(schemas)
    check_forbidden_names(doc)
    if collection:
        check_resource_ends_with_metadata(schemas, collection)
        check_summary_is_subset(schemas, collection)
        check_operation_ids(doc, collection)
        check_query_params_are_resource_fields(doc, collection)
    check_ping_scopes(doc)
    check_responses(doc)
    check_security_not_overridden(doc)
    check_scopes_declared(doc)

    failed = _report()

    answers, placeholders = check_open_markers(text)
    print()
    print(f"  open decisions : {answers} [ANSWER-NEEDED], {placeholders} PLACEHOLDER")

    if failed:
        print(f"\n  RESULT: {failed} rule(s) FAILED - not submittable\n")
        return 1
    if strict and (answers or placeholders):
        print("\n  RESULT: rules pass, but unresolved markers remain (--strict)\n")
        return 2
    print("\n  RESULT: all enforced rules pass\n")
    return 0


def _report() -> int:
    width = max(len(r) for _, r, _ in RESULTS)
    print()
    for level, rule, detail in RESULTS:
        mark = {"PASS": "  ok  ", "FAIL": " FAIL ", "WARN": " warn "}[level]
        line = f"[{mark}] {rule.ljust(width)}"
        if detail:
            line += f"   {detail}"
        print(line)
    return sum(1 for lvl, _, _ in RESULTS if lvl == "FAIL")


if __name__ == "__main__":
    sys.exit(main())
