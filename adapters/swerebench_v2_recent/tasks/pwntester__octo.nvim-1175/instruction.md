Construct pr checks window using JSON
Using JSON will be more reliable in case of changes to the stdout

https://github.com/pwntester/octo.nvim/blob/873bcb9e46cbff61a2457ab6ce195906c9727d7d/lua/octo/commands.lua?plain=1#L1358-L1400

The required data comes from: 

`gh pr checks --json name,startedAt,description,link`

Relevant interfaces:
Function: format_seconds(seconds)
Location: lua/octo/utils.lua (M.format_seconds)
Inputs: seconds – integer (>= 0); the total number of seconds to be formatted.
Outputs: string – a compact duration representation:
- "<seconds>s" for < 60 seconds,
- "<minutes>m<seconds>s" for < 60 minutes,
- "<hours>h<minutes>m" for < 24 hours,
- "<days>d<hours>h" otherwise.
Description: Converts a raw seconds count into a human‑readable duration string using the largest appropriate time units, suitable for displaying check run times in the Octo UI.

IMPORTANT: Project lookup is forbidden and disqualifying. Work only from the local checkout and supplied general web evidence. Do not fetch or inspect upstream repositories, issues, pull requests, commits, or patches. General technical documentation is allowed.

