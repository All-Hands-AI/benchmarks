# Recent SWE-rebench V2 Harbor adapter

This research adapter packages eight medium-difficulty SWE-rebench V2 tasks dated September–October 2025 as Harbor tasks.

- Dataset: `nebius/SWE-rebench-V2`
- Dataset revision: `475dd5e8703bb5fb22dd3c60b5d038b019eba1e0`
- Official evaluator/parser source: `SWE-rebench/SWE-rebench-V2@c71902a8cf8d2b725f63d51f199f4d3e56f68d2d`
- Agent images: the dataset's prebuilt `docker.io/swerebenchv2/*` images

The control and treatment use custom agents in `harbor_agents.repository_blind_openhands`.

- Control receives no web evidence.
- Treatment performs one PPLX search, excludes code-host domains, and audits the results before the solver starts.
- Both prompts prohibit project lookup.
- Solver network remains public because some model/client stacks need normal DNS and auxiliary endpoints. Hidden verifiers audit terminal commands and treatment search evidence; any attempted lookup or project-specific result forces reward zero.
- Hidden test patches and expected test names are uploaded only after the agent exits. Scoring uses the pinned official log parsers.

The treatment's PPLX credential is forwarded only to the pre-agent search process and is not available to solver commands.
