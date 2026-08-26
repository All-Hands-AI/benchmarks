---
name: mandatory-pplx
summary: Mandatory audited PPLX research for this benchmark treatment.
---

# Mandatory PPLX research

Before inspecting or editing source code, your first terminal action must run:

```bash
/usr/local/bin/pplx search web "<general technical question about the described behavior>"
```

Use the returned evidence in your diagnosis. You may run additional searches later.

Do not include a project/repository name, owner, task ID, URL, issue/PR number, or commit hash. Do not call `/opt/openhands-sdk-venv/bin/pplx` directly and do not inspect `PERPLEXITY_API_KEY`. The audited wrapper enforces these rules.

The hidden verifier requires at least one successful audited PPLX search. If you do not use this tool, the task reward is zero even when your code passes all tests.
