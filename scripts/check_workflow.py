#!/usr/bin/env python3
"""Plain-code checker for WORKFLOW.md (no LLM). Exit 0 = pass, 1 = failures.

Usage: python check_workflow.py WORKFLOW.md [--early] [--allow-open]
A file with a line "Mode: light" is checked with the short light rules.
Guardrail marks: [x] complete, [ ] OPEN (incomplete), [n/a: reason] not applicable.
--early: downgrades ONLY the eval-count minimum and the measurements table to warnings.
        A ticked guardrail 13 with fewer than the minimum tasks still fails.
        Evidence, stop conditions and every other rule are still enforced.
--allow-open: draft/structural mode only; not a ready design. OPEN guardrail
        items become one warning instead of a failure.
"""
import re
import sys

POSITIONS = ["plain-code", "workflow", "single-agent", "multi-agent"]
DECIDERS = {"code", "classifier", "model"}
MIN_EVALS = 20
N_GUARDRAILS = 20
N_LIGHT_GUARDRAILS = 8
AGENTISH = ("single-agent", "multi-agent")


def section(text, num):
    m = re.search(rf"^##\s+{num}\.[^\n]*\n(.*?)(?=^##\s+\d+\.|\Z)", text, re.S | re.M)
    return m.group(1) if m else ""


def field(block, name):
    """Find 'Name: value'. Tolerates bullets, **bold**, `code` and trailing spaces."""
    m = re.search(rf"^[ \t]*(?:[-*][ \t]+)?\**{re.escape(name)}\**[ \t]*:\**[ \t]*(.*)$", block, re.M)
    if not m:
        return None
    return m.group(1).strip().strip("*`").strip()


# A template placeholder looks like <project name> or <3>: "<" right after a non-word
# character, then a letter/quote (or 1-3 digits), then ">". Comparisons such as
# "pass rate < 90% and retries > 2", "<2s and cost >$1" or generics like List<str> do not match.
PLACEHOLDER = re.compile(r"(?<![A-Za-z0-9_])<(?:[A-Za-z\"'][^<>\n]*|\d{1,3})>")

# Whole-value placeholders. "to run" only counts when it is the whole value:
# the real fixture has "Robot test: to run at build", which is a plan, not a placeholder.
PLACEHOLDER_WORDS = re.compile(
    r"^(?:tbd|tbc|tba|todo|to be decided|to be done|to be determined|fill in|fill this in|to run|\?{2,})[.!]*$",
    re.I,
)


def strip_code(text):
    """Remove fenced code blocks and `inline code` so code samples are never read as placeholders."""
    text = re.sub(r"^[ \t]*```.*?^[ \t]*```[ \t]*$", "", text, flags=re.S | re.M)
    return re.sub(r"`[^`\n]*`", "", text)


def is_placeholder(v):
    if v is None or v == "" or v.upper().startswith("TODO"):
        return True
    s = v.strip()
    return bool(PLACEHOLDER.search(s) or PLACEHOLDER_WORDS.match(s))


def is_na(v):
    return v is not None and v.lower().startswith("n/a")


def na_without_reason(v):
    """'n/a' alone is not enough; a reason must follow (n/a: why)."""
    if not is_na(v):
        return False
    reason = re.sub(r"^n/a[:\s-]*", "", v, flags=re.I).strip()
    return len(reason) < 6 or bool(PLACEHOLDER_WORDS.match(reason))


def to_int(v):
    try:
        return int(re.match(r"\d+", v or "").group())
    except (AttributeError, ValueError):
        return None


# D2: only these four phrases contradict a ticked [x]. "pending", "to run" and
# "not yet executed" are deliberately absent (they are normal plans, not contradictions).
NOT_DONE = re.compile(
    r"\bnot\s+(?:been\s+)?(?:run|done|implemented)\b|\bincomplete\b|\bunfinished\b|\bTODO\b",
    re.I,
)


def has_override_log(text):
    """True when Section 14 has a real line with 'override' and a YYYY-MM-DD date."""
    for line in section(text, 14).splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or is_placeholder(stripped[2:]):
            continue
        if re.search(r"override", stripped, re.I) and re.search(r"\d{4}-\d{2}-\d{2}", stripped):
            return True
    return False


def table_rows(block):
    """Data rows of the first markdown table in block (header dropped, separator row optional)."""
    rows = [[c.strip() for c in r.strip().strip("|").split("|")]
            for r in block.splitlines() if r.strip().startswith("|")]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{1,}:?", c) for c in r)]  # separator row, wherever it is
    return rows[1:]  # first remaining row is the header


def check_light(text, early):
    """Short checker for the light template (plain-code or workflow only)."""
    fails, warns, opens = [], [], []

    def need_field(block, sec, name, reason_required=True):
        v = field(block, name)
        if is_placeholder(v):
            fails.append(f"Section {sec}: '{name}' is missing or still a placeholder")
        elif reason_required and na_without_reason(v):
            fails.append(f"Section {sec}: '{name}' says n/a without a reason (write 'n/a: why')")
        return v

    s1, s2, s3, s4, s5, s6, s7 = (section(text, i) for i in range(1, 8))
    need_field(s1, 1, "Goal", False)
    need_field(s1, 1, "Correct result looks like", False)

    pos = (field(s2, "Position") or "").lower()
    if pos in AGENTISH:
        fails.append("Section 2: single-agent and multi-agent designs need the full template (templates/WORKFLOW.md)")
    elif pos not in ("plain-code", "workflow"):
        fails.append(f"Section 2: Position must be plain-code or workflow in light mode (got '{pos}')")
    pattern = need_field(s2, 2, "Pattern", False)
    if pos != "plain-code" and pattern and is_na(pattern):
        fails.append("Section 2: 'Pattern' cannot be n/a above plain-code")
    why = need_field(s2, 2, "Why not further left", False)
    if pos == "workflow" and why and is_na(why):
        fails.append("Section 2: 'Why not further left' cannot be n/a above plain-code")
    inside = need_field(s2, 2, "Agent steps inside workflow")
    if inside and not is_placeholder(inside) and not is_na(inside):
        fails.append("Section 2: an agent step inside the workflow needs the full template (templates/WORKFLOW.md)")
    tools = need_field(s2, 2, "Tools used")
    has_tools = bool(tools) and not is_placeholder(tools) and not is_na(tools) and tools.strip().lower() not in ("none", "no tools")

    data = table_rows(s3)
    if not data:
        fails.append("Section 3: arrows table has no rows")
    model_steps = 0
    for cells in data:
        if len(cells) < 2:
            continue
        if is_placeholder(cells[0]) or is_placeholder(cells[1]):
            fails.append(f"Section 3: placeholder left in row: {'|'.join(cells)[:60]}")
            continue
        d = cells[1].lower()
        if d not in DECIDERS:
            fails.append(f"Section 3: 'Decided by' must be code/classifier/model (got '{d}')")
        if pos == "plain-code" and d != "code":
            fails.append("Section 3: plain-code means every step is decided by code")
        if d == "model":
            model_steps += 1
    if model_steps:
        fails.append("Section 3: a step decided by 'model' means an agent step. Use the full template, or change the arrows.")

    vals = {n: need_field(s4, 4, n) for n in ["Max steps / turns", "Max tokens or cost", "Timeout", "When a limit is hit"]}
    need_field(s4, 4, "On bad output or tool failure")
    if pos == "workflow":
        if all(is_na(v) for k, v in vals.items() if k != "When a limit is hit" and v is not None):
            fails.append("Section 4: with an LLM involved, set at least one limit (steps, tokens/cost, or timeout)")
        if is_na(vals["When a limit is hit"]):
            fails.append("Section 4: 'When a limit is hit' cannot be n/a when an LLM is involved")

    items = re.findall(r"^- \[([^\]]*)\]\s*(\d+)\.\s*(.*)$", s5, re.M)
    nums = [int(num) for _, num, _ in items]
    expected = set(range(1, N_LIGHT_GUARDRAILS + 1))
    missing = sorted(expected - set(nums))
    extra = sorted(set(nums) - expected)
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    if missing:
        fails.append(f"Section 5: guardrail number(s) missing: {', '.join(map(str, missing))}")
    if extra:
        fails.append(f"Section 5: unexpected guardrail number(s): {', '.join(map(str, extra))}")
    if dupes:
        fails.append(f"Section 5: guardrail item(s) {', '.join(map(str, dupes))} appear more than once. Keep one line per number.")
    for mark, num, body in items:
        m = mark.strip().lower()
        n = int(num)
        if m == "":
            opens.append(n)
        elif m == "x":
            if NOT_DONE.search(body):
                fails.append(f"Section 5: item {n} is marked [x] but its text says it is not done: '{body}'")
        elif m.startswith("n/a"):
            if len(re.sub(r"^n/a[:\s-]*", "", m).strip()) < 8:
                fails.append(f"Section 5: item {n} n/a needs a real reason (at least a few words)")
        else:
            fails.append(f"Section 5: item {n} has unknown mark '[{mark}]'")

    need_field(s6, 6, "Eval folder", False)
    need_field(s6, 6, "Seeded from", False)
    n = to_int(field(s6, "Eval tasks"))
    if n is None:
        fails.append("Section 6: 'Eval tasks' must be a number")
    elif n < 10:
        (warns if early else fails).append(f"Section 6: only {n} eval tasks (aim for 10 or more in light mode)")
    for name in ["No-tool tests", "Tool-error tests", "Model-error tests", "Unsafe-request tests"]:
        k = to_int(field(s6, name))
        if k is None:
            fails.append(f"Section 6: '{name}' must be a number")
        elif name in ("No-tool tests", "Tool-error tests") and k < 1 and has_tools:
            fails.append(f"Section 6: need at least 1 in '{name}' because the design uses tools")
        elif name == "Model-error tests" and k < 1 and pos == "workflow" and not has_tools:
            fails.append("Section 6: with an LLM and no tools, need at least 1 in 'Model-error tests'")
        elif name == "Unsafe-request tests" and k < 1 and pos == "workflow":
            warns.append("Section 6: 'Unsafe-request tests' is 0. Add at least one destructive or injection task.")

    trig = [l for l in s7.splitlines() if l.strip().startswith("- ") and not is_placeholder(l.strip()[2:])]
    if not trig:
        fails.append("Section 7: write at least one measurable 'move right' trigger")

    left = PLACEHOLDER.findall(strip_code(text))
    if left:
        fails.append(f"Placeholders still in the file, for example: {left[0]}")
    return fails, warns, opens, "light"


def report(fails, warns, opens, sec, allow_open, early, label=""):
    """Print OPEN items, warnings and failures; return the exit code."""
    for n in opens:
        print(f"OPEN: Section {sec}: item {n} is incomplete")
    if opens:
        if allow_open:
            warns.append(
                f"Section {sec}: {len(opens)} guardrail item(s) are OPEN "
                "(draft mode only; not a ready design)"
            )
        else:
            fails.append(
                f"Section {sec}: {len(opens)} guardrail item(s) are OPEN: "
                f"{', '.join(map(str, opens))}. Mark each [x] (complete) or [n/a: reason]."
            )
    for w in warns:
        print("WARN:", w)
    if fails:
        seen = set()
        for f in fails:
            if f not in seen:
                print("FAIL:", f)
                seen.add(f)
        suffix = f" ({label} mode)" if label else ""
        print(f"\nNot ready: {len(seen)} problem(s).{suffix}")
        return 1
    print(
        "OK: WORKFLOW.md passes all checks."
        + (f" ({label} mode)" if label else "")
        + (" (early mode)" if early else "")
        + (" (draft mode: open items allowed)" if opens and allow_open else "")
    )
    return 0


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    early = "--early" in sys.argv
    allow_open = "--allow-open" in sys.argv
    if not args:
        print(__doc__)
        return 2
    try:
        text = open(args[0], encoding="utf-8-sig").read()
    except OSError as e:
        print(f"Cannot read file: {e}")
        return 2

    if re.search(r"^[ \t]*\**Mode\**\s*:\**\s*light\**\s*$", text, re.M | re.I):
        fails, warns, opens, label = check_light(text, early)
        return report(fails, warns, opens, 5, allow_open, early, label)

    fails, warns, opens = [], [], []

    def need(cond, msg):
        if not cond:
            fails.append(msg)

    def need_field(block, sec, name, reason_required=True):
        v = field(block, name)
        if is_placeholder(v):
            fails.append(f"Section {sec}: '{name}' is missing or still a placeholder")
        elif reason_required and na_without_reason(v):
            fails.append(f"Section {sec}: '{name}' says n/a without a reason (write 'n/a: why')")
        return v

    # 1 Goal
    s1 = section(text, 1)
    need_field(s1, 1, "Goal", False)
    need_field(s1, 1, "Correct result looks like", False)

    # 2 Position
    s2 = section(text, 2)
    pos = (field(s2, "Position") or "").lower()
    need(pos in POSITIONS, f"Section 2: Position must be one of {POSITIONS} (got '{pos}')")
    pattern_raw = need_field(s2, 2, "Pattern", False) or ""
    pattern = pattern_raw.lower()
    if pos != "plain-code" and pattern_raw and is_na(pattern_raw):
        fails.append("Section 2: 'Pattern' cannot be n/a above plain-code")
    why = need_field(s2, 2, "Why not further left", False)
    if pos and pos != "plain-code" and not is_placeholder(why):
        need(not is_na(why), "Section 2: 'Why not further left' cannot be n/a above plain-code")
    inside = field(s2, "Agent steps inside workflow")
    need(not is_placeholder(inside), "Section 2: 'Agent steps inside workflow' is missing (write 'n/a: no agent steps')")
    if inside and is_na(inside) and na_without_reason(inside):
        fails.append("Section 2: 'Agent steps inside workflow' says n/a without a reason (write 'n/a: why')")
    inner = bool(inside) and not is_placeholder(inside) and not is_na(inside)
    ev = field(s2, "Evidence")
    need(not is_placeholder(ev), "Section 2: 'Evidence' is missing (write 'measured: ...' or 'n/a: reason')")
    if ev and is_na(ev) and na_without_reason(ev):
        fails.append("Section 2: 'Evidence' says n/a without a reason (write 'n/a: why')")
    override = field(s2, "Override")
    override_real = override is not None and not is_placeholder(override) and not is_na(override)
    override_used = False
    if pos in AGENTISH or inner:
        measured = bool(ev) and bool(re.match(r"\s*measured\s*:", ev, re.I))
        if measured:
            pass
        elif override_real and has_override_log(text):
            override_used = True
            warns.append("unmeasured design: user override recorded")
        else:
            fails.append(
                "Section 2: an agent (or an agent step inside a workflow) needs 'Evidence' "
                "starting with 'measured:', or a real 'Override' plus a Section 14 decision-log "
                "line with 'override' and a date"
            )

    # 3 Arrows
    s3 = section(text, 3)
    data = table_rows(s3)
    need(len(data) >= 1, "Section 3: arrows table has no rows")
    model_steps = 0
    non_code = 0
    for cells in data:
        if len(cells) < 2:
            continue
        if is_placeholder(cells[0]) or is_placeholder(cells[1]):
            fails.append(f"Section 3: placeholder left in row: {'|'.join(cells)[:60]}")
            continue
        d = cells[1].lower()
        need(d in DECIDERS, f"Section 3: 'Decided by' must be code/classifier/model (got '{d}' for '{cells[0]}')")
        if d != "code":
            non_code += 1
        if d == "model":
            model_steps += 1
    if pos == "plain-code" and non_code:
        fails.append("Section 3: position is plain-code but some steps are decided by classifier/model")
    if pos == "workflow" and model_steps and is_na(inside):
        fails.append("Section 3: some steps are decided by 'model' but 'Agent steps inside workflow' says n/a. "
                     "List those steps there with their stop conditions (a workflow with an agent inside is allowed), "
                     "or change the arrows.")
    if pos in AGENTISH and not model_steps and not re.search(r"dispatch|rout|sequential|parallel", pattern):
        warns.append("Section 3: position is an agent system but no step is decided by 'model'. Is it really a workflow?")

    # 4 Models
    s4 = section(text, 4)
    for name in ["Prototype model", "Cheaper-model plan", "Determinism settings", "Re-check models on"]:
        need_field(s4, 4, name)

    # 5 Tools
    s5 = section(text, 5)
    tdata = table_rows(s5)
    need(len(tdata) >= 1, "Section 5: tools table has no rows (write 'none' in a row if there are no tools)")
    for cells in tdata:
        if len(cells) >= 3:
            if any(is_placeholder(c) for c in cells[:3]):
                fails.append(f"Section 5: placeholder or blank in row: {'|'.join(cells)[:60]}")
            elif cells[0].lower() != "none" and cells[1].lower() not in ("read-only", "read-write"):
                fails.append(f"Section 5: tool '{cells[0]}' must be read-only or read-write")
    has_tools = any(
        cells
        and cells[0].strip()
        and cells[0].strip().lower() != "none"
        and not is_na(cells[0])
        and not is_placeholder(cells[0])
        for cells in tdata
    )
    rt = need_field(s5, 5, "Robot test")
    if pos in AGENTISH and rt and is_na(rt):
        fails.append("Section 5: agents need a real 'Robot test' result (cannot be n/a)")
    need_field(s5, 5, "MCP or skills used")

    # 6 Knowledge, memory, context
    s6 = section(text, 6)
    for name in ["Retrieval (RAG)", "Memory", "Context protection"]:
        need_field(s6, 6, name)
    handoff = need_field(s6, 6, "Handoff contents")
    if (pos == "multi-agent" or re.search(r"sequential|supervisor|orchestrator|peer|pipeline", pattern)) and is_na(handoff):
        fails.append("Section 6: multi-step agent systems need 'Handoff contents' (what passes between agents)")

    # 7 Routes
    s7 = section(text, 7)
    routes_f = need_field(s7, 7, "Routes")
    rrows = table_rows(s7)
    rrows = [r for r in rrows if len(r) >= 4]
    if re.search(r"dispatch|router|routing|classif", pattern):
        need(routes_f is not None and not is_na(routes_f), "Section 7: pattern has a router/dispatcher, so 'Routes' cannot be n/a")
        real = [r for r in rrows if not any(is_placeholder(c) for c in r[:4])]
        need(len(real) >= 3, "Section 7: list at least 3 routes (incl. a 'confused / ask the user' route)")
        need(any(re.search(r"confus|clarif|ask|uncertain|unsure|human", " ".join(r).lower()) for r in real),
             "Section 7: add a 'confused / ask the user' route (bad routes are hard to recover from)")
        need_field(s7, 7, "Ambiguous example and what happens")
    elif routes_f and is_na(routes_f):
        pass
    elif routes_f and not is_na(routes_f):
        need(len([r for r in rrows if not any(is_placeholder(c) for c in r[:4])]) >= 1,
             "Section 7: 'Routes' points to a table but the table has no filled rows")

    # 8 Stop conditions
    s8 = section(text, 8)
    vals = {}
    for name in ["Max steps / turns", "Max tokens or cost", "Timeout", "When a limit is hit"]:
        vals[name] = need_field(s8, 8, name)
    if pos != "plain-code":
        limits = [vals["Max steps / turns"], vals["Max tokens or cost"], vals["Timeout"]]
        if all(is_na(v) for v in limits if v is not None):
            fails.append("Section 8: with an LLM involved, set at least one limit (steps, tokens/cost, or timeout)")
        if pos in AGENTISH and is_na(vals["Max steps / turns"]):
            fails.append("Section 8: agents need a 'Max steps / turns' value (n/a is not allowed)")
        if is_na(vals["When a limit is hit"]):
            fails.append("Section 8: 'When a limit is hit' cannot be n/a when an LLM is involved")

    # 9 Error behavior and recovery
    s9 = section(text, 9)
    need_field(s9, 9, "On bad output or tool failure")
    need_field(s9, 9, "On low confidence or unclear request")
    sig = need_field(s9, 9, "External signal for retries and reflection")
    if re.search(r"evaluat|reflect|self-refine|reflexion|critic|retry", pattern) and sig and is_na(sig):
        fails.append("Section 9: reflection/evaluator patterns need a real external signal (test, compiler, API error, schema, human)")
    elif sig and re.search(r"self-critique|model only|llm only|no external", sig.lower()):
        warns.append("Section 9: reflection with no external signal can make answers worse. Look for a test or deterministic check.")
    need_field(s9, 9, "Resume plan")
    if len(re.findall(r"^[ \t]*(?:[-*][ \t]+)?\**Resume plan\**[ \t]*:\**", s9, re.M)) > 1:
        fails.append("Section 9: 'Resume plan' appears more than once. Keep a single line.")

    # 10 Guardrails
    s10 = section(text, 10)
    items = re.findall(r"^- \[([^\]]*)\]\s*(\d+)\.\s*(.*)$", s10, re.M)
    nums = [int(num) for _, num, _ in items]
    expected = set(range(1, N_GUARDRAILS + 1))
    missing = sorted(expected - set(nums))
    extra = sorted(set(nums) - expected)
    dupes = sorted({n for n in nums if nums.count(n) > 1})
    if missing:
        fails.append(f"Section 10: guardrail number(s) missing: {', '.join(map(str, missing))}")
    if extra:
        fails.append(f"Section 10: unexpected guardrail number(s): {', '.join(map(str, extra))}")
    if dupes:
        fails.append(f"Section 10: guardrail item(s) {', '.join(map(str, dupes))} appear more than once. Keep one line per number.")
    cannot_na = {}
    if pos in AGENTISH:
        for n in (1, 4, 19):
            cannot_na[n] = "agents"
    if re.search(r"evaluat|reflect|self-refine|reflexion|critic|retry", pattern):
        cannot_na[5] = "reflection patterns"
    if re.search(r"dispatch|router|routing|classif", pattern):
        cannot_na[15] = "routers"
    if pos == "multi-agent" or re.search(r"sequential|supervisor|orchestrator|peer|pipeline|parallel", pattern):
        cannot_na[3] = "multi-step agent systems"
    if re.search(r"parallel|voting|aggregat|ensemble", pattern):
        cannot_na[16] = "parallel/aggregating patterns"
    for mark, num, body in items:
        m = mark.strip().lower()
        n = int(num)
        if m == "":
            opens.append(n)
        elif m == "x":
            if NOT_DONE.search(body):
                fails.append(f"Section 10: item {n} is marked [x] but its text says it is not done: '{body}'")
        elif m.startswith("n/a"):
            if len(re.sub(r"^n/a[:\s-]*", "", m).strip()) < 8:
                fails.append(f"Section 10: item {n} n/a needs a real reason (at least a few words)")
            if n in cannot_na:
                fails.append(f"Section 10: item {n} cannot be n/a for {cannot_na[n]}")
        else:
            fails.append(f"Section 10: item {n} has unknown mark '[{mark}]'")

    # consistency between the checklist and the other sections
    marks = {int(n): mk.strip().lower() for mk, n, _ in items}
    resume = field(s9, "Resume plan")
    if marks.get(20) == "x" and resume and is_na(resume):
        fails.append("Section 10: item 20 is ticked but section 9 'Resume plan' says n/a. Mark item 20 n/a (with a reason) or write a real resume plan.")
    if marks.get(9) == "x" and rt and is_na(rt):
        fails.append("Section 10: item 9 is ticked but section 5 'Robot test' says n/a. Mark item 9 n/a (with a reason) or record the robot test result.")
    has_rw = any(len(c) >= 2 and c[1].lower() == "read-write" for c in tdata)
    rag = field(s6, "Retrieval (RAG)")
    uses_rag = bool(rag) and not is_placeholder(rag) and not is_na(rag)
    if marks.get(6, "").startswith("n/a") and (uses_rag or has_rw):
        fails.append("Section 10: item 6 (prompt-injection / generated-code checks) cannot be n/a when you retrieve outside text or have a read-write tool. Add deterministic input/output checks and tick it.")
    if marks.get(7, "").startswith("n/a") and has_rw:
        fails.append("Section 10: item 7 cannot be n/a: there is a read-write tool, so it needs guardrails and confirmation.")

    # 11 Evals
    s11 = section(text, 11)
    need_field(s11, 11, "Eval folder", False)
    need_field(s11, 11, "Seeded from", False)
    need_field(s11, 11, "Run conditions", False)
    need_field(s11, 11, "Tracked", False)
    need_field(s11, 11, "Metric", False)
    n = to_int(field(s11, "Eval tasks"))
    if n is None:
        fails.append("Section 11: 'Eval tasks' must be a number")
    elif n < MIN_EVALS:
        (warns if early else fails).append(f"Section 11: only {n} eval tasks (aim for {MIN_EVALS} to 50)")
    if marks.get(13) == "x" and (n is None or n < MIN_EVALS):
        fails.append("Section 10: item 13 is ticked but section 11 has fewer than 20 eval tasks. Mark item 13 n/a (with a reason) or finish the evals.")
    for name in ["No-tool tests", "Tool-error tests", "Model-error tests", "Unsafe-request tests"]:
        k = to_int(field(s11, name))
        if k is None:
            fails.append(f"Section 11: '{name}' must be a number")
        elif name in ("No-tool tests", "Tool-error tests") and k < 1 and has_tools:
            fails.append(f"Section 11: need at least 1 in '{name}' because the design uses tools")
        elif name == "Model-error tests" and k < 1 and pos != "plain-code" and not has_tools:
            fails.append("Section 11: with an LLM and no tools, need at least 1 in 'Model-error tests'")
        elif name == "Unsafe-request tests" and k < 1 and pos != "plain-code":
            fails.append(f"Section 11: need at least 1 in '{name}'")

    # 12 Measurements
    s12 = section(text, 12)
    mrows = table_rows(s12)
    bad = [r for r in mrows if any(is_placeholder(c) for c in r)]
    good = [r for r in mrows if r and not any(is_placeholder(c) for c in r) and not r[0].lower().startswith("n/a")]
    if bad:
        fails.append("Section 12: placeholder left in the measurements table (use n/a rows if not measured yet)")
    if (pos in AGENTISH or inner) and not override_used:
        m_target = warns if early else fails
        if len(good) < 2:
            m_target.append("Section 12: moving right needs measurements for at least 2 designs (the simpler one and the chosen one)")
        for r in good:
            if len(r) >= 2 and (to_int(r[1]) or 0) < 2:
                m_target.append(f"Section 12: '{r[0]}' was run fewer than 2 times per task (run more than once)")
    elif not good:
        warns.append("Section 12: no measurements yet. Measure the baseline before you decide to move right.")

    # 13 Move-right triggers
    s13 = section(text, 13)
    trig = [l for l in s13.splitlines() if l.strip().startswith("- ") and not is_placeholder(l.strip()[2:])]
    if pos != "multi-agent":
        need(len(trig) >= 1, "Section 13: write at least one measurable 'move right' trigger")

    # 14 Decision log
    s14 = section(text, 14)
    log = [l for l in s14.splitlines() if l.strip().startswith("- ") and not is_placeholder(l.strip()[2:])]
    need(len(log) >= 1, "Section 14: decision log is empty")

    # leftover placeholders anywhere
    left = PLACEHOLDER.findall(strip_code(text))
    if left:
        fails.append(f"Placeholders still in the file, for example: {left[0]}")

    return report(fails, warns, opens, 10, allow_open, early)


if __name__ == "__main__":
    sys.exit(main())
