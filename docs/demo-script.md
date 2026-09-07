# Demo Script (under 5 minutes)

Run `./scripts/setup.sh`, add your `GROQ_API_KEY` to `.env`, then
`./scripts/seed_demo.sh` and `streamlit run dashboard/app.py` before you
start recording, so the diagram/graph is warm and nothing waits on a cold
start during the take.

**0:00-0:30 -- The problem**
"AI coding assistants autocomplete lines. They don't help you understand a
system, review a change with real context, catch a performance regression
before it ships, or keep architecture docs honest. Argus does all four,
grounded in one live map of the codebase."

**0:30-1:15 -- Live Codebase Memory + Architecture tab**
Show the sidebar's graph summary (modules/functions/calls/imports parsed
from `data/sample_repo`). Switch to the Architecture tab, click "Generate
diagram." Point out it's built structurally from real call edges, not
guessed by the LLM -- only the module descriptions are LLM-written.

**1:15-2:15 -- Review tab**
Select `reserve_stock` (it has a seeded bug: no check for negative
resulting stock). Click Review. Show that the review references its real
caller (`orders.create_order`), not just the function in isolation.

**2:15-3:15 -- Tests tab**
Select `has_duplicate_items`. Click "Generate & run tests." Show the
generated pytest code and the pass/fail result. If a first attempt fails,
narrate the retry live -- that's the LangGraph cycle, not a hidden retry.

**3:15-4:00 -- Performance tab**
Select `has_duplicate_items` again. Show the MEDIUM risk badge and that it
correctly caught the O(n^2) nested loop. Say the sentence: "today this is
a static heuristic; the roadmap is a text-to-text regression model trained
on our own CI history, following Akhauri & Song's 2025 Regression Language
Models work."

**4:00-4:40 -- Ask Argus tab**
Ask "what does create_order do?" live. Show the graph-grounded answer.

**4:40-5:00 -- Close**
One slide: what's built vs. roadmap (see README section on scope), and
the team.

## Fallback if the dashboard breaks live
Everything the dashboard calls is a plain Python function -- run the same
calls from a `python3` REPL (see the smoke-test snippets in
`tests/test_orchestrator.py` for the exact call shapes) as a backup.
