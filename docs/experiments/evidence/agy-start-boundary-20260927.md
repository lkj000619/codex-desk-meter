# Common startup boundary revision — 2026-09-27

User requested proceeding after the r07 review. Apply the same startup instructions to
every candidate: current working directory is the checkout; read environment and finite
permission rules with native file tools first; run one permitted command per call;
do not inspect parent directories or locate operator manifests outside the checkout.
Runner already validates operator manifest/profile/receipt before delivering the prompt.
The previous prompt ambiguously asked the agent to stop if those outside files were missing.
Responsibility now explicitly belongs to the runner, without removing its validation.

The permission policy, model, timeout, product requirements and evaluation criteria are unchanged.
No implementation hints or runtime follow-up are supplied. This is a new prompt/baseline input
condition. Prior pilots remain immutable, excluded from ranking, and cannot be pooled with the
new input condition. Future quantitative comparison requires matching baseline and input hashes
across candidates and repetitions. A pilot failure remains a failure; startup clarification
does not establish product readiness.
