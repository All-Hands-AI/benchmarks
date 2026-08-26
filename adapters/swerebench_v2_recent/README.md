# Recent SWE-rebench V2 Harbor adapter

This research adapter packages eight medium-difficulty SWE-rebench V2 tasks dated September–October 2025 as Harbor tasks.

- Dataset: `nebius/SWE-rebench-V2`
- Dataset revision: `475dd5e8703bb5fb22dd3c60b5d038b019eba1e0`
- Official evaluator/parser source: `SWE-rebench/SWE-rebench-V2@c71902a8cf8d2b725f63d51f199f4d3e56f68d2d`
- Agent images: the dataset's prebuilt `docker.io/swerebenchv2/*` images

The control and treatment use custom agents in `harbor_agents.repository_blind_openhands`.

- Control receives no web evidence.
- Treatment must invoke `/usr/local/bin/pplx search web ...` from its own coding trajectory at least once. It may invoke the tool repeatedly.
- The wrapper blocks project identifiers, URLs, issue numbers, commit hashes, direct code-host results, and unsupported PPLX operations. Every query and response is logged.
- Both prompts prohibit project lookup.
- Solver network remains public because some model/client stacks need normal DNS and auxiliary endpoints. Hidden verifiers audit terminal commands and PPLX logs; any lookup attempt, contaminated result, wrapper bypass, credential inspection, or absence of a successful PPLX call forces reward zero.
- Hidden test patches and expected test names are uploaded only after the agent exits. Scoring uses the pinned official log parsers.

The treatment credential is available to the custom agent process so its audited wrapper can call PPLX. Arbitrary direct PPLX calls or attempts to inspect the credential are disqualifying.
