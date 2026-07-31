---
name: pplx-required
description: Require a Perplexity web search before solving every evaluation task.
---

# Required Perplexity research

For every task, you must use Perplexity web search before making any changes or
attempting a solution. This requirement applies even if the task appears fully
self-contained.

1. Extract a short, task-specific search query from the user instruction. Use
   distinctive technical terms, filenames, error messages, APIs, or concepts
   from the task; do not use a generic query.
2. Run at least one `pplx search web "<task-specific query>"` command in the
   terminal.
3. Read the result and use it to inform your solution. If it is not useful,
   briefly state why in your reasoning and continue with the task.

`PERPLEXITY_API_KEY` is already available in the agent environment. Do not run
interactive authentication commands and never print or expose the key.
