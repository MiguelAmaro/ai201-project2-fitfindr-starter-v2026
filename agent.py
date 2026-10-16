"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from tools import search_listings, suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── parsing the query ─────────────────────────────────────────────────────────

_PRICE_RE = re.compile(
    r"\b(?:under|below|less than|no more than|up to|at most|max(?:imum)?)(?:\s+of)?\s*\$?\s*(\d+(?:\.\d{1,2})?)(?:\s*(?:dollars?|bucks|usd)\b)?"
    r"|\$\s*(\d+(?:\.\d{1,2})?)"
    r"|\b(\d+(?:\.\d{1,2})?)\s*(?:dollars?|bucks|usd)\b(?:\s+(?:max(?:imum)?|or less|or under|or below))?",
    re.I,
)
_SIZE_RE = re.compile(r"\bsize\s+([A-Za-z0-9]+(?:/[A-Za-z0-9]+)?(?:\.\d+)?)", re.I)
_PREFIX_RE = re.compile(
    r"^\s*(?:(?:i(?:'m| am)?\s+)?(?:looking for|searching for)|find me|find|show me)\s+", re.I
)


def parse_query(query: str) -> dict:
    """Regex-parse a description, size and price ceiling; returns the same result every time."""
    text = query or ""

    max_price = None
    price_match = _PRICE_RE.search(text)
    if price_match:
        max_price = float(next(g for g in price_match.groups() if g))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size = None
    size_match = _SIZE_RE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[: size_match.start()] + " " + text[size_match.end():]

    text = _PREFIX_RE.sub("", text)
    description = re.sub(r"\s+", " ", text).strip(" ,.-")
    return {"description": description, "size": size, "max_price": max_price}


# ── planning loop ─────────────────────────────────────────────────────────────

def _search(parsed: dict) -> list[dict]:
    """Search over MCP, falling back to the local tool if MCP is unavailable."""
    try:
        from mcp_client import call_tool

        return call_tool(
            "search_listings",
            {
                "description": parsed["description"],
                "size": parsed["size"],
                "max_price": parsed["max_price"],
            },
        ) or []
    except Exception:  # noqa: BLE001
        return search_listings(parsed["description"], parsed["size"], parsed["max_price"])


def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session. Check session["error"] first.

    Branch rule: if search returns nothing, set session["error"] naming what the
    user could change and return before suggest_outfit.
    """
    session = new_session(query, wardrobe)
    steps = 0

    try:
        steps += 1
        trace.check_iterations(steps)
        parsed = parse_query(query)
        session["parsed"] = parsed
        trace.step("parse_query", inputs=query, returned=parsed)

        steps += 1
        trace.check_iterations(steps)
        results = _search(parsed)
        session["search_results"] = results
        trace.step(
            "search_listings (via MCP)",
            inputs=parsed,
            returned=results,
            note=f"{len(results)} match(es)",
        )

        if not results:
            session["error"] = _nothing_found_message(parsed)
            trace.step("branch", note="search returned []: stopping before suggest_outfit")
            return session

        steps += 1
        trace.check_iterations(steps)
        session["selected_item"] = results[0]
        trace.step("select_item", returned=session["selected_item"])

        steps += 1
        trace.check_iterations(steps)
        session["outfit_suggestion"] = suggest_outfit(
            session["selected_item"], session["wardrobe"]
        )
        trace.step(
            "suggest_outfit",
            inputs=session["selected_item"],
            returned=session["outfit_suggestion"],
            note=f"{len(session['wardrobe'].get('items') or [])} wardrobe item(s)",
        )

        steps += 1
        trace.check_iterations(steps)
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
        trace.step(
            "create_fit_card",
            inputs=session["selected_item"],
            returned=session["fit_card"],
        )

    except ModelUnavailable as exc:
        session["error"] = (
            "The model couldn't be reached, so the outfit and caption steps "
            f"didn't run. The search worked — {len(session['search_results'])} "
            "listing(s) were found. Check GEMINI_API_KEY in your .env, then run "
            f"the same query again.\nWhat the service said: {exc}"
        )
        trace.step("model unavailable", note="stopping, search results kept")

    return session


def _nothing_found_message(parsed: dict) -> str:
    """Name only the filters the user actually set when suggesting what to change."""
    tried = [f"description {parsed['description']!r}"]
    if parsed["size"]:
        tried.append(f"size {parsed['size']}")
    if parsed["max_price"] is not None:
        tried.append(f"under ${parsed['max_price']:g}")

    suggestions = ["try broader words — 'jacket' finds more than 'cropped corduroy jacket'"]
    if parsed["size"]:
        suggestions.append("drop the size, or try a neighbouring one")
    if parsed["max_price"] is not None:
        suggestions.append(f"raise the price ceiling above ${parsed['max_price']:g}")

    return (
        "Nothing in the listings matched " + ", ".join(tried) + ".\n"
        "Things to change: " + "; ".join(suggestions) + "."
    )


def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )




