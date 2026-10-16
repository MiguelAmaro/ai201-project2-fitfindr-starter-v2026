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

**Branch rule:** If `search_listings` returns an empty list, `run_agent()` sets `session["error"]` to a message from `_nothing_found_message()`, then returns. The message names only the filters the user actually set (description, size, price ceiling) and what to change. It does not call either model-backed tool. Otherwise, it selects the first result and continues through outfit suggestion and fit-card creation.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** `agent.py::parse_query` uses regular expressions rather than a model call, so it costs nothing and returns the same answer every time. It extracts a size after `size` (uppercased) and a price after terms such as `under`, `below`, `up to`, or `max`, or after a `$`; the price is stored as a float. It removes those matches and a leading request phrase (such as `looking for`) from the remaining description. Its limit is unseen phrasing: "nothing over thirty dollars" parses to no price, so the ceiling is silently ignored.

**What moves through the session:** `new_session()` first stores the original `query` and `wardrobe`, with empty or `None` result fields. `run_agent()` stores `description`, `size`, and `max_price` in `parsed`, then stores the complete search return in `search_results`. `_search()` calls `search_listings` over MCP (`mcp_client.call_tool`) and falls back to the local function if MCP is unavailable. On a match it stores the first listing as `selected_item`, passes that item and `wardrobe` to `suggest_outfit()`, and stores the result in `outfit_suggestion`. It passes that string and the same selected listing to `create_fit_card()` and stores the result in `fit_card`. On no match, later fields remain `None`. Each step calls `trace.check_iterations()` and `trace.step()`, and a `ModelUnavailable` error is caught and written to `session["error"]` with the search results kept.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Here are two cute outfit ideas featuring the Y2K Baby Tee with Butterfly Print, styled using pieces straight from your wardrobe:

### Outfit 1: Bratz Doll Streetwear (Y2K Casual)
Play up the early 2000s aesthetic by pairing the fitted, cropped butterfly tee with oversized denim for that classic Y2K silhouette contrast.

* **Top:** Y2K Baby Tee — Butterfly Print
* **Bottoms:** Baggy straight-leg jeans (dark wash)
* **Outerwear:** Black cropped zip hoodie (wear it open or loosely draped over the shoulders)
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

### Outfit 2: Sweet & Grunge (Vintage Contrast)
Balance the sweet, cottagecore-leaning butterfly graphic and pink/purple tones with some tougher, grungy pieces for a cool girl off-duty look.

* **Top:** Y2K Baby Tee — Butterfly Print
* **Outerwear:** Vintage black denim jacket
* **Bottoms:** Wide-leg khaki trousers
* **Accessories:** Brown leather belt (to cinch the trousers)
* **Shoes:** Black combat boots

  Fit card: Channeling serious Bratz doll streetwear vibes with this Y2K Baby Tee with Butterfly Print! Grab this early 2000s staple for $18.0 on depop to nail that perfect sweet-yet-grungy outfit contrast.

2 model calls this session, 836 prompt + 294 output tokens
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"

[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"

Here are two streetwear-inspired outfits featuring your new **Vintage Levi's 501 Jeans (Medium Wash)** and pieces directly from your wardrobe:

### Outfit 1: Casual & Classic Streetwear
*Lean into the vintage, effortless aesthetic by pairing the classic medium wash denim with clean basics and a touch of edge.*

* **Bottoms:** Vintage Levi's 501 Jeans (Medium Wash)
* **Top:** White ribbed tank top (tucked in to highlight the waist of the 501s)
* **Outerwear:** Vintage black denim jacket worn over the top
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag

### Outfit 2: Cozy Contrast
*Play with proportions by pairing the straight-leg 501s with an extra-cozy, oversized layer and rugged boots.*

* **Bottoms:** Vintage Levi's 501 Jeans (Medium Wash)
* **Top:** Oversized grey crewneck sweatshirt
* **Accessories:** Brown leather belt (threaded through the jeans to break up the grey and blue)
* **Shoes:** Black combat boots (letting the hems of the 501s sit neatly right at the top of the boots)
* **Bag:** Black crossbody bag
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"

Channeling that effortless streetwear vibe with these Vintage Levi's 501 Jeans — Medium Wash paired with crisp white sneakers. They're giving the ultimate classic denim energy for everyday wear. Snag them on depop for $38.0!
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
- *What I changed:* I kept the unit 3 version limited to the Milestone 5 requirements. In unit 4 I compared it against the instructor's `agent.py` and merged in `trace.step` calls, a per-step `check_iterations`, `ModelUnavailable` handling, a separate `parse_query`, a specific empty-search message, and an MCP fallback. I kept my own price regex (accepts "under 30" with no `$`) and my leading-phrase stripping.
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
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item passed on equals `selected_item` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions exact price and a style tag | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result at or under the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**, pasted as text, naming the file and function
that produced it. Produced by `run_eval.py::main` calling `agent.py::run_agent`
(`results/run_2026-10-15_1648_before.md`, scenario "matching query completes", try 1):

```
[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)

Fit card (tools.py::create_fit_card):
Channeling peak early 2000s downtown-cool vibes with this Y2K Baby Tee — Butterfly Print, styled with baggy denim and chunky sneakers. Grab it on depop for just $18.0 to complete your retro wardrobe!
```

PASS/FAIL for each try was decided by a scoring pass over the same scenarios
(caching off, five tries each): criterion 3 compared `session["selected_item"]`
against the dict actually received by `suggest_outfit` (both `lst_032` in all five
tries); criterion 4 checked the card text for the price and a style tag; criterion 5
checked every returned price (`[18.0, 15.0, 19.0]`) against `max_price` 20.0.

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
| 1 | Matching query completes all three tools | 4 of 5 | MET | 5 of 5 tries returned a fit card with no `session["error"]`. |
| 2 | Impossible query stops before tool 2 | 5 of 5 | MET | 5 of 5 tries set `session["error"]`, left `fit_card` as `None`, and never called `suggest_outfit`. |
| 3 | Item passed on equals `selected_item` | 5 of 5 | MET | In 5 of 5 tries the dict received by `suggest_outfit` equaled `session["selected_item"]` (`lst_032`). |
| 4 | Fit card mentions exact price and a style tag | 4 of 5 | MET | 5 of 5 cards contained `$18.0` and at least one of the item's tags (e.g. "Y2K"). |
| 5 | Every result at or under the price ceiling | 5 of 5 | MET | 5 of 5 searches for "graphic tee under $20" returned only 15.0, 18.0 and 19.0. |

**Diagnoses**

No criterion was missed, so there is nothing to diagnose. Two caveats: criteria 1 and 4
each ran one query five times, so they test model variation but not other phrasings or items.
Criterion 5 ran against 3 results, and an earlier choice, "jacket under $25", returned nothing
and would have passed vacuously, so it was replaced.



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
python app.py ask "vintage graphic tee under $30" --trace

[1] parse_query
      in:  vintage graphic tee under $30
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    10 match(es)
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] suggest_outfit
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Here are two cute outfit ideas featuring the Y2K Baby Tee with Butterfly Print, styled using pieces straight f…
      →    10 wardrobe item(s)
[5] create_fit_card
      in:  Y2K Baby Tee — Butterfly Print ($18.0, depop)
      out: Channeling serious Bratz doll streetwear vibes with this Y2K Baby Tee with Butterfly Print! Grab this early 20…

2 model calls this session, 836 prompt + 294 output tokens
```

**Empty search**

```
python app.py ask "designer ballgown size XXS under $5" --trace

[1] parse_query
      in:  designer ballgown size XXS under $5
      out: dict with keys: description, size, max_price
[2] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
      →    0 match(es)
[3] branch
      →    search returned []: stopping before suggest_outfit

  Nothing in the listings matched description 'designer ballgown', size XXS, under $5.
Things to change: try broader words — 'jacket' finds more than 'cropped corduroy jacket'; drop the size, or try a neighbouring one; raise the price ceiling above $5.

0 model calls this session
```

The empty trace has 3 steps and the happy path has 5; the branch stops before `suggest_outfit`.

**On the MCP move:** `agent.py::_search` calls `mcp_client.call_tool("search_listings", ...)`, which starts `mcp_server.py` over stdio. The server registers one `search_listings` tool that wraps `tools.py::search_listings`. Behavior did not change: the same 10 listings come back. The catch is that `_search` falls back to the local function on any error, and the `(via MCP)` trace label prints either way. Before I installed the `mcp` package, `call_tool` raised `No module named 'mcp'`, and every earlier run, including the "before" run log, silently used the local fallback. After `pip install "mcp>=1.0,<2.0"`, a direct `call_tool` call returned the 3 listings for "graphic tee" under $20, and the traces above were captured with MCP working.



---

## Failure Modes

**1. Nothing found.** Handled by the branch in `agent.py::run_agent`; see the empty-search trace above. The run stops with 0 model calls and a message naming what to change.

**2. Empty wardrobe.** `run_agent("denim jacket under $50", get_empty_wardrobe())` completes. `tools.py::suggest_outfit` falls back to general styling advice, and `session["error"]` is `None`:

```
[4] suggest_outfit
      in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
      out: ### General Styling Advice  Since this is a **cropped, light-wash denim jacket with structured shoulders**, it…
      →    0 wardrobe item(s)
[5] create_fit_card
      in:  Denim Jacket — Light Wash, Cropped ($42.0, poshmark)

ERROR: None
CARD: Channeling some serious 80s and 90s streetwear energy with this cropped, light-wash denim jacket featuring the coolest structured shoulders! I scored it on poshmark for just $42.0, and it's the ultimate vintage-vibed blank canvas for everyday layering.
```

**3. Model unavailable.** Run with `GEMINI_API_KEY` set to a bad value for one process. `agent.py::run_agent` catches `ModelUnavailable`, keeps the search results, and leaves `outfit_suggestion` and `fit_card` as `None`:

```
[3] select_item
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[4] model unavailable
      →    stopping, search results kept
ERROR: The model couldn't be reached, so the outfit and caption steps didn't run. The search worked — 10 listing(s) were found. Check GEMINI_API_KEY in your .env, then run the same query again.
What the service said: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com.
results kept: 10
OUTFIT: None
CARD: None
```

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** In `agent.py`, `_PRICE_RE` now also accepts `no more than`, a trailing `dollars`/`bucks`/`usd` after a number, and a bare `N dollars [max | or less | or under]`. `parse_query` reads whichever capture group matched.

**Which failure it was meant to fix:** The "before" run had no misses, so I probed the parser with other phrasings and added a second criterion 5 scenario to `scenarios.py`, `"graphic tee, 20 dollars max"`. Measured before the fix, it failed 5 of 5: `parse_query` returned `max_price: None` because the price regex needed a keyword *before* the number. The ceiling was dropped, so `search_listings` returned `[18.0, 24.0, 15.0, 19.0, 27.0, 26.0]` and three results were over $20. The failure is in the parser, not the search tool, which correctly filters whatever `max_price` it receives.

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item passed on equals `selected_item` | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card mentions exact price and a style tag | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Every result at or under the price ceiling (`"graphic tee, 20 dollars max"`) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

The original criterion 5 query (`"graphic tee under $20"`) also passed 5 of 5 after the change.

**Did it help, and how do I know:** Yes, for the targeted phrasing: criterion 5 on `"graphic tee, 20 dollars max"` went from 0 of 5 (before) to 5 of 5 (after), with `max_price` now `20.0` and results `[18.0, 15.0, 19.0]`. Criteria 1 to 4 were unchanged at 5 of 5, so the new regex did not break the existing queries. `"vintage graphic tee under $30"` and `"designer ballgown size XXS under $5"` still parse as before. The tries for the new scenario were run through `parse_query` and `agent.py::_search`, not the model, since the price check does not depend on it. It is a deterministic parser, so five tries return identical results. The five-try format mainly confirms the result is stable.

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is currently missed, but one gap remains. `parse_query` ignores number words, so `"graphic tee under twenty dollars"` still returns `max_price: None` and the ceiling is silently dropped, which would fail criterion 5. I stopped at digit phrasings because a word-to-number table is a bigger change for a phrasing that no scenario exercises yet. Criteria 1 and 4 also each use a single query, so they say little about other items or phrasings.


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
