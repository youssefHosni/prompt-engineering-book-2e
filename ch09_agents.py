"""Chapter 9 — From Prompts to Agents.

  9.1  one general tool beats five specific ones
  9.4  the routing experiment — and the confound that ruined the first version:
       the tool *names* gave away the answer, so the model was reading the
       labels, not the question.

`run_python` evaluates a single expression. It is sandboxed here only by
restriction, which is not a sandbox; Chapter 15 §15.4 is the honest version.
"""
import json

from peb import ask

run_python = {
    "name": "run_python",
    "description": ("Evaluate a single Python expression over the depot log and "
                    "return its value. The variable `rows` is a list of dicts, "
                    "each with keys: depot (str), pallets (int), product (str). "
                    "Only an expression, not statements."),
    "input_schema": {
        "type": "object",
        "properties": {"code": {"type": "string"}},
        "required": ["code"],
    },
}

ROWS = [
    {"depot": "Leeds",  "pallets": 120, "product": "cement"},
    {"depot": "Leeds",  "pallets": 80,  "product": "timber"},
    {"depot": "Hull",   "pallets": 140, "product": "cement"},
    {"depot": "Hull",   "pallets": 60,  "product": "sand"},
    {"depot": "Oldham", "pallets": 72,  "product": "timber"},
]

# §9.4 — deliberately opaque names. The model must route on the *description*,
# not on a name that restates the question.
ROUTING_TOOLS = [
    {"name": "tool_a", "description": "Return the current stock level for one product code."},
    {"name": "tool_b", "description": "Return the delivery status of one order reference."},
    {"name": "tool_c", "description": "Return the opening hours of one depot."},
]

ROUTING_CASES = [
    ("Is the Leeds depot open on Saturday?", "tool_c"),
    ("Where has order KL-449021 got to?",    "tool_b"),
    ("How many units of CEM-22 do we hold?", "tool_a"),
]


# An allowlist, not an empty namespace. Blanking __builtins__ entirely also
# removes len, sum and round, which leaves the tool unable to answer any of the
# questions it exists for -- a restriction so tight the feature stops working is
# a bug, not security.
SAFE_BUILTINS = {
    "len": len, "sum": sum, "min": min, "max": max, "round": round,
    "sorted": sorted, "set": set, "list": list, "dict": dict, "tuple": tuple,
    "abs": abs, "any": any, "all": all, "enumerate": enumerate, "zip": zip,
    "str": str, "int": int, "float": float, "bool": bool,
}


def evaluate(code):
    """Restriction, not isolation. See §15.4 -- a denylist of substrings is a
    speed bump. Anything that matters runs in a real sandbox."""
    if any(tok in code for tok in ("import", "__", "open(", "exec", "eval")):
        return "refused: expression only"
    try:
        return repr(eval(code, {"__builtins__": SAFE_BUILTINS}, {"rows": ROWS}))
    except Exception as e:
        return f"error: {e}"


def general_tool():
    print("§9.1  one general tool over a fixed table\n")
    questions = [
        "How many pallets of cement in total?",
        "Which depot moved the most pallets?",
        "What was the average customer satisfaction score for cement deliveries?",
    ]
    for q in questions:
        prompt = (f"You may call one tool.\n\nTool: {json.dumps(run_python)}\n\n"
                  f"Question: {q}\n\nReply with JSON: "
                  f'{{"code": "<expression>"}} or {{"answer": "<why you cannot>"}}')
        text, _ = ask(prompt, max_tokens=400)
        try:
            call = json.loads(text[text.index("{"):text.rindex("}") + 1])
        except Exception:
            print(f"  {q}\n    unparseable: {text.strip()[:60]!r}\n"); continue
        if "code" in call:
            print(f"  {q}\n    code   {call['code'][:70]}\n    result {evaluate(call['code'])}")
        else:
            print(f"  {q}\n    declined: {call['answer'][:70]}")
        print()
    print("  The third question has no answer in the data. That is the point:\n"
          "  a tool that can compute anything will happily compute nonsense\n"
          "  unless declining is an available move.\n")


def routing_without_giveaway_names():
    print("§9.4  routing on descriptions, not on names\n")
    right = 0
    for q, expect in ROUTING_CASES:
        prompt = (f"Choose exactly one tool. Reply with its name only.\n\n"
                  f"{json.dumps(ROUTING_TOOLS, indent=2)}\n\nRequest: {q}")
        text, _ = ask(prompt, max_tokens=100)
        got = text.strip().split()[0].strip(".,'\"") if text.strip() else ""
        right += (got == expect)
        print(f"  {q[:44]:<46} -> {got:<8} (want {expect})")
    print(f"\n  {right}/{len(ROUTING_CASES)} correct. If the names had been "
          f"`get_hours`,\n  `get_order_status` and `get_stock`, this would measure nothing.\n")


if __name__ == "__main__":
    general_tool()
    routing_without_giveaway_names()
