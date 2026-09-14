# migrate-eval

`migrate-eval` is an evaluation framework for LLM-assisted code migration using executable tests as the correctness oracle.

The current benchmark evaluates Java-to-Go migration on the validated HumanEval-X Go set.

## Milestone 4 — Full Evaluation

Validated benchmark size:

- 163 tasks
- `Go/95` excluded because of nondeterministic Go map iteration
- iteration 0 = initial migration
- iterations 1–3 = test-driven repair attempts

### Results

| Model | Iteration 0 | Iteration 1 | Iteration 2 | Iteration 3 | Improvement | Initial failures repaired |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.6 Terra | 93.9% | 98.8% | 99.4% | 99.4% | +5.5 pp | 9/10 (90.0%) |
| Qwen2.5-Coder 14B | 72.4% | 84.7% | 85.9% | 86.5% | +14.1 pp | 23/45 (51.1%) |

### Main Findings

GPT-5.6 Terra achieved the strongest overall result:

- 153/163 tasks passed without repair
- 162/163 passed after up to three repair iterations
- 9 of 10 initial failures were repaired

Qwen2.5-Coder 14B benefited more in absolute percentage points from the repair loop:

- 118/163 tasks passed without repair
- 141/163 passed after up to three repair iterations
- 23 of 45 initial failures were repaired

Most repair gains occurred during the first repair iteration for both models.

### Failure Taxonomy

Initial failures:

| Model | Compile Error | Test Fail | Total |
|---|---:|---:|---:|
| GPT-5.6 Terra | 6 | 4 | 10 |
| Qwen2.5-Coder 14B | 30 | 15 | 45 |

Final failures:

| Model | Compile Error | Test Fail | Total |
|---|---:|---:|---:|
| GPT-5.6 Terra | 0 | 1 | 1 |
| Qwen2.5-Coder 14B | 9 | 13 | 22 |

### Evaluation Plots

#### Pass Rate vs Repair Iteration

![Pass rate vs repair iteration](results/plots/pass_rate_vs_iteration.png)

#### Failure Taxonomy

![Failure taxonomy](results/plots/failure_taxonomy.png)

### Telemetry

| Model | Attempts | Fresh Attempts | Cache Hits | Input Tokens | Output Tokens | Mean Fresh Latency |
|---|---:|---:|---:|---:|---:|---:|
| GPT-5.6 Terra | 176 | 176 | 0 | 60,917 | 34,052 | 3.980 s |
| Qwen2.5-Coder 14B | 256 | 227 | 29 | 101,202 | 32,010 | 5.070 s |

For Qwen, cached attempts reuse the completion associated with an identical model/prompt pair. Fresh-call latency therefore excludes `cache_hit == true` attempts.
