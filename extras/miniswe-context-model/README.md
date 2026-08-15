# MiniSWE context model

This small optional package provides a `LitellmModel` subclass for long-running
MiniSWE evaluations. It retains the system prompt, task, and newest complete
assistant/tool turns while eliding old turns before a request exceeds the configured
serialized-history budget.

Install it in the MiniSWE tool environment and select:

```text
openhands_miniswe_context_model.model.ContextSafeLitellmModel
```

The `model.max_history_chars` config field defaults to 500,000 characters and can
be overridden by the benchmark's agent configuration.
