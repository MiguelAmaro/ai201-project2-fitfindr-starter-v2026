# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

FitFindr takes a clothing search request and looks for matching thrift listings using the item's description, an optional size, and an optional price ceiling. If it finds something, it uses the first match and the user's wardrobe to suggest outfits, then creates a short fit-card caption. If nothing matches, it returns a message suggesting what the user could change instead of trying to style an item that was not found.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Loads the listings and ranks items by keyword overlap with the description, after applying the optional size and inclusive maximum-price filters. Size matching uses size tokens, so `M` matches `S/M` without relying on substring matching.
- **Inputs:** `description: str`; `size: str | None = None`; `max_price: float | None = None`.
- **Returns:** A list of up to `config.SEARCH_RESULT_LIMIT` listing dictionaries, highest keyword-overlap score first. Each dictionary has `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.
- **When it has nothing:** Returns `[]` if no listing passes the filters and has at least one keyword in common with the description.

### `suggest_outfit`

- **What it does:** Calls `generate()` to suggest one or two outfits for a listing, using named pieces from the user's wardrobe when available.
- **Inputs:** `new_item: dict` (a listing); `wardrobe: dict` (with an `items` list).
- **Returns:** A non-empty `str` containing outfit suggestions or styling advice.
- **When it has nothing:** An empty wardrobe gets general styling advice instead. If the model response is empty or whitespace, the tool returns fallback styling advice.

### `create_fit_card`

- **What it does:** Calls `generate()` to write a 2–4 sentence fit-card caption from the outfit and listing details, asking it to mention the item, exact price, platform, and style or vibe.
- **Inputs:** `outfit: str`; `new_item: dict` (a listing).
- **Returns:** The `str` returned by `generate()` for a non-empty outfit.
- **When it has nothing:** If `outfit` is empty or whitespace, returns a descriptive message without calling the model.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings()` returns an empty list, `run_agent()` sets `session["error"]` with suggestions to change the description, remove the size filter, or raise the price limit, then returns. It does not call either model-backed tool. Otherwise, it selects the first result and continues through outfit suggestion and fit-card creation.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** `run_agent()` uses regular expressions. It extracts a size after `size` and a numeric price after terms such as `under`, `below`, `up to`, or `max`; the price is stored as a float. It removes those matched constraints and a supported leading request phrase (such as `looking for`) from the remaining description.

**What moves through the session:** `new_session()` first stores the original `query` and `wardrobe`, with empty or `None` result fields. `run_agent()` stores `description`, `size`, and `max_price` in `parsed`, then stores the complete search return in `search_results`. On a match it stores the first listing as `selected_item`, passes that item and `wardrobe` to `suggest_outfit()`, and stores the result in `outfit_suggestion`. It passes that string and the same selected listing to `create_fit_card()` and stores the result in `fit_card`. On no match, later fields remain `None`; the loop also checks its iteration count with `trace.check_iterations()`.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

[Paste the real terminal output here after running the command.]
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

[Paste the real terminal output here after running the command.]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

[Paste the real terminal output here after running the command.]
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

[Paste the real terminal output here after running the command.]
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked GitHub Copilot to implement the three `tools.py` functions from the provided starter specifications.
- *What came back:* Copilot helped generate listing search, wardrobe-aware outfit suggestions, and fit-card generation, including the specified empty-result and empty-input behavior.
- *What I changed:* The Copilot-generated implementation was refined to include listing size in search keyword matching and to return fallback styling advice for an empty model response. I did not hand-write the generated implementations.
- *Verification:* I ran the three standalone tool commands and checked their real outputs separately from code generation.

**Moment 2**

- *What I asked for:* I asked GitHub Copilot to implement the Milestone 5 `run_agent()` planning loop from its starter TODO.
- *What came back:* Copilot helped generate regex-based query parsing, session updates, the empty-search early return, and the successful search-to-outfit-to-fit-card path.
- *What I changed:* I kept the implementation limited to the Milestone 5 requirements; it does not add Unit 4 trace-step instrumentation or `ModelUnavailable` handling.
- *Verification:* Separately, I ran `python agent.py` and mocked checks for successful tool order and the empty-search path, including `fit_card` remaining `None`.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
