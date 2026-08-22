# Evaluation basics

Upload a small approved procedure set, run every question in `golden_set.json` against `POST /ask`, and record: retrieval hit, presence of expected terms, grounded/no-answer decision and latency. Human reviewers then submit `POST /feedback`. The `/evaluations` endpoint exposes baseline operational metrics. Do not treat lexical term matching as proof of correctness; it is a smoke test before human review.


