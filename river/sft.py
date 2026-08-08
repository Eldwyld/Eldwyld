"""Supervised fine-tuning smoke test: teach the model to prefix `test-` to every word.

A trivial pattern, so a tiny dataset and ~15 steps are enough to learn it — the
point is to verify the whole training loop end to end.

    uv run sft.py
"""

import river_client as river

from _bootstrap import get_client, pick_base_model

PREFERRED = "Qwen/Qwen3.6-35B-A3B-FP8"

client = get_client()
BASE = pick_base_model(client, PREFERRED)
tok = river.load_tokenizer(base_model=BASE)
EOS = tok.eos_token_id

train_inputs = [
    "hello world",
    "good morning sunshine",
    "the quick brown fox",
    "i love programming",
    "open the pod bay doors",
    "river flows to the sea",
]

held_out = ["hello world", "the lazy dog sleeps"]


def target_for(x):
    return " ".join("test-" + w for w in x.split())


def render(x):
    return f"Input: {x}\nOutput:"


def make_datum(x):
    """Tokenize prompt + completion into one sequence, with the prompt masked out.

    `weights` is 0.0 across the prompt so the loss only counts completion tokens,
    offset by one because position i predicts ids[i+1].
    """
    prompt_ids = tok(render(x), add_special_tokens=False)["input_ids"]
    completion_ids = tok(" " + target_for(x), add_special_tokens=False)["input_ids"] + [EOS]
    ids = prompt_ids + completion_ids
    target_tokens = ids[1:] + [EOS]
    weights = [0.0] * (len(prompt_ids) - 1) + [1.0] * (len(completion_ids) + 1)
    return {"input_ids": ids, "target_tokens": target_tokens, "weights": weights}


batch = [make_datum(x) for x in train_inputs]

with client.session(project="sft-prefix") as session:
    model = session.create_model(base_model=BASE, lora=river.LoraConfig(rank=32))
    print("model_id:", model.model_id)

    for _ in range(15):
        fb = model.forward_backward(batch, loss_fn="cross_entropy")
        model.optim_step(lr=2e-4, grad_clip_norm=1.0)
        print(f"step {model.step:2d}  loss={fb.metrics['loss']:.4f}")

    # Sample from the live trained weights (no checkpoint needed).
    print("\nlive weights:")
    for x in held_out:
        out = model.sample(render(x), max_tokens=16, temperature=0.0, stop=["\n"])
        print(f"  {x!r} -> {out[0][0].text!r}")

    # Save an inference checkpoint and confirm it reproduces the behavior.
    ckpt = model.save_weights("prefix", mode="inference")
    print("\nsaved:", ckpt.path)
    for x in held_out:
        out = session.sample(
            render(x), base_model=BASE, checkpoint=ckpt,
            max_tokens=16, temperature=0.0, stop=["\n"],
        )
        print(f"  {x!r} -> {out[0][0].text!r}")
