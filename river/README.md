# River API

Scripts for sampling from and fine-tuning hosted models through
[River](https://river.ai).

## Setup

River's client requires **Python 3.12+**. The easiest way to get that is
[uv](https://docs.astral.sh/uv/), which reads `pyproject.toml` and manages the
interpreter and virtualenv for you:

```bash
# from the repo root
uv sync --project river
```

Then add your API key. Create one on the **API Keys** page of the River console
and put it in a local `.env` file:

```bash
cp river/.env.example river/.env
# open river/.env and paste your key in
```

`.env` is gitignored, so the key stays on your machine and never gets committed.
If you'd rather use a plain environment variable, that works too and takes
precedence:

```bash
export RIVER_API_KEY="rv_..."
```

## Verify it works

```bash
uv run --project river river/check_setup.py
```

This checks the key, connects, lists the models your key can use, and generates
one short completion. If it prints `Setup is working.` you're done.

## Scripts

| Script | What it does |
| --- | --- |
| `check_setup.py` | Key → connection → model list → one sample. Run this first. |
| `sft.py` | Supervised fine-tuning smoke test: learns to prefix `test-` to every word, in ~15 steps. |
| `rl.py` | RL on GSM8K with group-relative advantages. One epoch is 29 steps; reward climbs ~0.04 → ~0.93. |

```bash
uv run --project river river/sft.py

# rl.py needs the extra dataset deps, and is a real training run —
# start small before committing to a full epoch
uv run --project river --extra rl river/rl.py --steps 2
```

## Notes

- **Model access is per-account.** `client.get_capabilities()` returns the live
  list your key can use, which may be shorter than the public catalog. The
  scripts call it and fall back to an available model rather than hard-coding a
  name that might be rejected.
- **Requests are asynchronous.** `client.sample(...)` and the other high-level
  methods submit and poll for you. The `submit_*` variants return a `request_id`
  immediately if you want to run several requests in parallel.
- **LoRA rank maxes out at 32.** Anything higher is rejected.
- **Bigger batches are faster.** There's fixed per-step overhead, so packing more
  sequences into one `forward_backward` or `sample` call beats many small calls.
- **Checkpoints are durable.** A `river://` path is all you need to resume — in a
  different session, process, or machine. `mode="training"` keeps optimizer state
  so training continues where it left off; `mode="inference"` is PEFT weights
  only, for serving.
