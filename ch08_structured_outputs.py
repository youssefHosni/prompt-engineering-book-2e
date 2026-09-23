"""Chapter 8 — Structured Outputs.

  8.1  "reply with JSON only", and what actually comes back
  8.2  the same request with a schema
  8.4  tool definitions are prompts, and the description is the prompt
  8.5  the tool loop

Tool use is where provider APIs genuinely differ, so §8.4 and §8.5 use the
Anthropic SDK directly rather than the book's `ask()` wrapper.
"""
import json
import re

from peb import ask
from peb.fixtures import REVIEW

naive = """Extract order_ref and fault_count from this review as JSON.
Reply with JSON only.

Review: Drip tray warped after a week. Order ref KL-449021."""

schema = {
    "type": "object",
    "properties": {
        "order_ref":       {"type": ["string", "null"],
                            "description": "Format KL- followed by six digits, or null"},
        "days_to_deliver": {"type": ["integer", "null"]},
        "fault_count":     {"type": "integer"},
        "faults":          {"type": "array", "items": {"type": "string"}},
        "sentiment":       {"type": "string",
                            "enum": ["positive", "negative", "mixed"]},
    },
    "required": ["order_ref", "days_to_deliver", "fault_count",
                 "faults", "sentiment"],
    "additionalProperties": False,
}

get_order = {
    "name": "get_order",
    "description": ("Look up exactly one order using its full reference. "
                    "The reference format is KL- followed by six digits. "
                    "Use only when the user has supplied such a reference."),
    "input_schema": {
        "type": "object",
        "properties": {"order_ref": {"type": "string"}},
        "required": ["order_ref"],
        "additionalProperties": False,
    },
}

search_orders = {
    "name": "search_orders",
    "description": ("Search orders by customer name, product or date range when no "
                    "order reference is available. Returns up to 20 matches."),
    "input_schema": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
        "additionalProperties": False,
    },
}

ORDERS = {"KL-449021": {"ref": "KL-449021", "product": "Nordic 400",
                        "ordered": "2026-03-03", "delivered": "2026-03-11"}}


def run_tool(name, args):
    if name == "get_order":
        return json.dumps(ORDERS.get(args["order_ref"], {"error": "not found"}))
    if name == "search_orders":
        return json.dumps(list(ORDERS.values()))
    return json.dumps({"error": f"unknown tool {name}"})


def json_only_is_not_a_guarantee():
    print("§8.1  'reply with JSON only', 8 runs\n")
    clean = 0
    for i in range(8):
        text, _ = ask(naive, max_tokens=300)
        stripped = text.strip()
        is_clean = stripped.startswith("{") and stripped.endswith("}")
        clean += is_clean
        if i == 0:
            print(f"  first reply: {stripped[:70]!r}")
    print(f"\n  parsed without repair: {clean}/8 — the fences are the usual culprit.\n")


def with_a_schema():
    print("§8.2  the same extraction, with the schema in the prompt\n")
    prompt = (f"Extract the fields defined by this JSON Schema from the review.\n"
              f"Reply with one JSON object and nothing else.\n\n"
              f"Schema:\n{json.dumps(schema, indent=2)}\n\nReview: ```{REVIEW}```")
    ok = 0
    for _ in range(8):
        text, _ = ask(prompt, max_tokens=700)
        m = re.search(r"\{.*\}", text, re.S)
        try:
            obj = json.loads(m.group(0))
            ok += set(schema["required"]) <= set(obj)
        except Exception:
            pass
    print(f"  valid against required keys: {ok}/8\n")


def the_tool_loop():
    print("§8.5  the tool loop\n")
    import anthropic
    client = anthropic.Anthropic()

    messages = [{"role": "user",
                 "content": "What did I order on KL-449021, and when did it arrive?"}]
    turns = 0
    while True:
        response = client.messages.create(
            model="claude-opus-5", max_tokens=1024,
            tools=[get_order, search_orders],
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            break
        turns += 1
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"  -> {block.name}({block.input})")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": run_tool(block.name, block.input),
                })
        messages.append({"role": "user", "content": results})

    final = "".join(b.text for b in response.content if b.type == "text")
    print(f"\n  after {turns} tool turn(s): {final.strip()[:240]}\n")


if __name__ == "__main__":
    json_only_is_not_a_guarantee()
    with_a_schema()
    try:
        the_tool_loop()
    except Exception as e:
        print(f"§8.5 needs an Anthropic key (tool use is provider-specific): {e}")
