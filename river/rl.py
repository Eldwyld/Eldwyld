"""RL on GSM8K with group-relative advantages and the importance_sampling loss.

For each question we sample a group of answers, reward the ones whose \\boxed{...}
matches the ground truth, turn rewards into group-relative advantages, and update
the policy. One epoch over GSM8K's 7,473 training questions is 29 steps.

This is a real training run — it costs real GPU time. Start with --steps 2.

    uv run --extra rl rl.py --steps 2
"""

import argparse
import re

import datasets
import river_client as river

from _bootstrap import get_client, pick_base_model

PREFERRED = "Qwen/Qwen3.6-35B-A3B-FP8"
BATCH_SIZE, GROUP_SIZE, MAX_TOKENS, LORA_RANK, LR = 256, 4, 128, 8, 4e-5


# ── GSM8K reward: 1.0 if the last \boxed{...} matches the ground-truth number ──
def extract_boxed(text):
    out, stack = [], []
    for i, ch in enumerate(text):
        if ch == "{":
            stack.append(i)
        elif ch == "}" and stack:
            s = stack.pop()
            if text[:s].endswith("\\boxed"):
                out.append(text[s + 1 : i])
    return out[-1] if out else None


def gsm8k_gt(answer_field):
    for line in reversed(answer_field.splitlines()):
        if line.strip().startswith("####"):
            return line.strip()[4:].strip().lstrip(":").replace(",", "").strip()
    return answer_field.strip()


def get_reward(response, answer_field):
    ext = extract_boxed(response)
    if ext is None:
        return 0.0

    def norm(s):
        s = s.replace(",", "").replace("$", "").replace(" ", "")
        m = re.search(r"-?\d+\.?\d*", s)
        return m.group(0) if m else s

    try:
        return 1.0 if float(norm(ext)) == float(norm(gsm8k_gt(answer_field))) else 0.0
    except ValueError:
        return 1.0 if norm(ext) == norm(gsm8k_gt(answer_field)) else 0.0


suffix = " Provide a numerical answer without units, written inside \\boxed{}."
fewshot = [
    {"role": "user", "content": "How many r's are in strawberry?" + suffix},
    {"role": "assistant", "content": (
        "Let's spell the word out and number all the letters: "
        "1) s 2) t 3) r 4) a 5) w 6) b 7) e 8) r 9) r 10) y. "
        "We have r's at positions 3, 8, and 9. \\boxed{3}")},
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=None,
                    help="number of steps to run (default: one full epoch, 29)")
    ap.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = ap.parse_args()

    client = get_client()
    model_name = pick_base_model(client, PREFERRED)
    tok = river.load_tokenizer(base_model=model_name)
    train_ds = datasets.load_dataset("openai/gsm8k", "main")["train"]

    batch_size = args.batch_size
    n_batches = len(train_ds) // batch_size
    n_steps = min(args.steps, n_batches) if args.steps else n_batches
    print(f"training {n_steps} step(s) of {batch_size} questions on {model_name}")

    with client.session(project="rl-gsm8k") as session:
        model = session.create_model(
            base_model=model_name,
            lora=river.LoraConfig(rank=LORA_RANK, train_unembed=True),
        )
        for step in range(n_steps):
            rows = train_ds.select(
                range(step * batch_size, step * batch_size + batch_size)
            )

            prompts, prompt_tok = [], []
            for q in rows["question"]:
                msgs = [*fewshot, {"role": "user", "content": q + suffix}]
                text = tok.apply_chat_template(
                    msgs, tokenize=False, add_generation_prompt=True,
                    enable_thinking=False)
                prompts.append(text)
                prompt_tok.append(tok.encode(text, add_special_tokens=False))

            groups = model.sample(
                prompts=prompts, num_samples=GROUP_SIZE, max_tokens=MAX_TOKENS,
                stop=["<|im_end|>"], seed=step * len(prompts) * GROUP_SIZE)

            train_data, all_rewards = [], []
            for ptok, samples, answer in zip(prompt_tok, groups, rows["answer"]):
                rewards = [get_reward(s.text, answer) for s in samples]
                mean_r = sum(rewards) / len(rewards)
                all_rewards.append(mean_r)
                if all(r == mean_r for r in rewards):
                    continue  # zero advantage across the group — nothing to learn
                ob = len(ptok)
                for s, r in zip(samples, rewards):
                    adv = r - mean_r
                    # Completion-aligned arrays start at ob-1 (the last prompt
                    # position predicts the first response token) and end with a
                    # trailing 0.0 for the no-next-token slot.
                    train_data.append({
                        "input_ids": ptok + s.tokens,
                        "attention_mask": [1] * (ob + len(s.tokens)),
                        "old_logprobs": [0.0] * (ob - 1) + s.logprobs + [0.0],
                        "advantages": [0.0] * (ob - 1) + [adv] * len(s.tokens) + [0.0],
                    })

            if train_data:
                model.forward_backward(train_data, loss_fn="importance_sampling")
                model.optim_step(lr=LR, beta1=0.9, beta2=0.95, eps=1e-8)

            reward = sum(all_rewards) / len(all_rewards) if all_rewards else 0.0
            print(f"[step {step:2d}] reward={reward:.3f}")

        ckpt = model.save_weights(f"gsm8k_step{model.step}", mode="training")
        print("saved:", ckpt.path)


if __name__ == "__main__":
    main()
