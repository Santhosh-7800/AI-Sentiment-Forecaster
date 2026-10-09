"""
QLoRA Fine-Tuning Pipeline for RoBERTa Sentiment Model
=======================================================
Uses 4-bit quantization (bitsandbytes) + LoRA adapters (peft) to fine-tune
`cardiffnlp/twitter-roberta-base-sentiment` on our domain-specific enriched data.

Requirements:
    pip install peft bitsandbytes accelerate datasets scikit-learn

Usage:
    python -m pipelines.finetune_sentiment
    python -m pipelines.finetune_sentiment --epochs 5 --lr 2e-4 --output models/sentiment_qlora

The saved adapter is automatically picked up by backend/llm/sentiment_engine.py.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("finetune_sentiment")

# ── Label mapping ─────────────────────────────────────────────────────────────
# Collapse 5-class pipeline labels → 3 RoBERTa classes
LABEL_COLLAPSE = {
    "very_positive": "Positive",
    "positive":      "Positive",
    "neutral":       "Neutral",
    "very_negative": "Negative",
    "negative":      "Negative",
}
LABEL2ID = {"Negative": 0, "Neutral": 1, "Positive": 2}
ID2LABEL = {v: k for k, v in LABEL2ID.items()}

BASE_MODEL   = "cardiffnlp/twitter-roberta-base-sentiment"
DEFAULT_OUT  = str(Path(__file__).resolve().parent.parent / "models" / "sentiment_qlora")
ENRICHED_DIR = Path(__file__).resolve().parent.parent / "data" / "enriched"


# ── Data loading ──────────────────────────────────────────────────────────────
def load_training_data(min_text_len: int = 15) -> pd.DataFrame:
    """Load the latest enriched parquet and build a clean 3-class training set."""
    candidates = sorted(ENRICHED_DIR.glob("enriched_*.parquet"), reverse=True)
    latest = ENRICHED_DIR / "enriched_latest.parquet"
    path = latest if latest.exists() else (candidates[0] if candidates else None)
    if path is None:
        raise FileNotFoundError(
            "No enriched parquet found. Run pipelines/sentiment_topic_pipeline.py first."
        )

    logger.info(f"Loading training data from {path}")
    df = pd.read_parquet(path)

    # Require text and label
    df = df.dropna(subset=["clean_text", "sentiment_label"])
    df = df[df["clean_text"].str.len() >= min_text_len].copy()

    # Map to 3-class label
    df["label_str"] = df["sentiment_label"].str.lower().str.strip().map(LABEL_COLLAPSE)
    df = df.dropna(subset=["label_str"])
    df["label"] = df["label_str"].map(LABEL2ID)

    logger.info(f"Training samples: {len(df)}")
    logger.info(f"Label distribution:\n{df['label_str'].value_counts().to_string()}")
    return df[["clean_text", "label", "label_str"]].reset_index(drop=True)


# ── QLoRA training ────────────────────────────────────────────────────────────
def finetune(
    output_dir: str  = DEFAULT_OUT,
    epochs: int      = 3,
    lr: float        = 2e-4,
    batch_size: int  = 16,
    max_length: int  = 128,
    lora_r: int      = 16,
    lora_alpha: int  = 32,
    lora_dropout: float = 0.05,
    val_split: float = 0.15,
    seed: int        = 42,
) -> str:
    """
    Fine-tune the RoBERTa sentiment model with QLoRA.

    Returns the path to the saved adapter directory.
    """
    # ── Lazy imports (heavy ML deps) ─────────────────────────────────────────
    try:
        import torch
        from datasets import Dataset
        from sklearn.metrics import accuracy_score, f1_score
        from transformers import (
            AutoTokenizer,
            AutoModelForSequenceClassification,
            TrainingArguments,
            Trainer,
            DataCollatorWithPadding,
            BitsAndBytesConfig,
            EarlyStoppingCallback,
        )
        from peft import (
            LoraConfig,
            get_peft_model,
            TaskType,
            prepare_model_for_kbit_training,
        )
    except ImportError as e:
        logger.error(
            f"Missing dependency: {e}\n"
            "Run: pip install peft bitsandbytes accelerate datasets scikit-learn"
        )
        sys.exit(1)

    # ── Check GPU ─────────────────────────────────────────────────────────────
    device      = "cuda" if torch.cuda.is_available() else "cpu"
    use_4bit    = device == "cuda"          # 4-bit quant only on GPU
    logger.info(f"Device: {device}  |  4-bit quantisation: {use_4bit}")

    # ── Load data ─────────────────────────────────────────────────────────────
    df = load_training_data()
    if len(df) < 20:
        raise ValueError(f"Only {len(df)} samples — need at least 20 to fine-tune.")

    # Train / validation split
    from sklearn.model_selection import train_test_split
    train_df, val_df = train_test_split(df, test_size=val_split, random_state=seed, stratify=df["label"])
    logger.info(f"Train: {len(train_df)}  |  Val: {len(val_df)}")

    train_ds = Dataset.from_pandas(train_df[["clean_text", "label"]].rename(columns={"clean_text": "text"}))
    val_ds   = Dataset.from_pandas(val_df[["clean_text", "label"]].rename(columns={"clean_text": "text"}))

    # ── Tokeniser ─────────────────────────────────────────────────────────────
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding=False,          # DataCollatorWithPadding handles padding per-batch
            max_length=max_length,
        )

    train_ds = train_ds.map(tokenize, batched=True, remove_columns=["text"])
    val_ds   = val_ds.map(tokenize,   batched=True, remove_columns=["text"])
    train_ds = train_ds.rename_column("label", "labels")
    val_ds   = val_ds.rename_column("label", "labels")

    collator = DataCollatorWithPadding(tokenizer=tokenizer)

    # ── 4-bit config (QLoRA) ──────────────────────────────────────────────────
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,     # nested quantisation for extra savings
        bnb_4bit_quant_type="nf4",          # NormalFloat4 — best for LLM weights
        bnb_4bit_compute_dtype=torch.float16,
    ) if use_4bit else None

    # ── Load base model ───────────────────────────────────────────────────────
    logger.info(f"Loading base model: {BASE_MODEL}")
    model = AutoModelForSequenceClassification.from_pretrained(
        BASE_MODEL,
        num_labels=3,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        quantization_config=bnb_config,     # None on CPU → full precision
        device_map="auto" if use_4bit else None,
        ignore_mismatched_sizes=True,
    )

    # ── Prepare for k-bit training (gradient checkpointing, cast norms, etc.) ──
    if use_4bit:
        model = prepare_model_for_kbit_training(model)

    # ── LoRA config ───────────────────────────────────────────────────────────
    # Target the self-attention query/value projections inside RoBERTa
    lora_config = LoraConfig(
        task_type=TaskType.SEQ_CLS,
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        target_modules=["query", "value"],   # RoBERTa attention projections
        modules_to_save=["classifier"],       # Always train the classification head
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # ── Metrics ───────────────────────────────────────────────────────────────
    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": float(accuracy_score(labels, preds)),
            "f1_macro": float(f1_score(labels, preds, average="macro", zero_division=0)),
        }

    # ── Training arguments ────────────────────────────────────────────────────
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(out_path / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.1,
        weight_decay=0.01,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        logging_steps=10,
        fp16=use_4bit,              # mixed precision on GPU
        dataloader_num_workers=0,   # safe for Windows
        report_to="none",           # disable wandb/tensorboard unless configured
        seed=seed,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    # ── Train ─────────────────────────────────────────────────────────────────
    logger.info("Starting QLoRA fine-tuning…")
    train_result = trainer.train()
    logger.info(f"Training complete: {train_result.metrics}")

    # ── Evaluate ──────────────────────────────────────────────────────────────
    eval_metrics = trainer.evaluate()
    logger.info(f"Final eval metrics: {eval_metrics}")

    # ── Save adapter + tokeniser ──────────────────────────────────────────────
    logger.info(f"Saving LoRA adapter to {out_path}")
    model.save_pretrained(str(out_path))
    tokenizer.save_pretrained(str(out_path))

    # Write a small config so sentiment_engine knows what base model was used
    config_path = out_path / "finetune_config.json"
    import json
    with open(config_path, "w") as f:
        json.dump(
            {
                "base_model":   BASE_MODEL,
                "label2id":     LABEL2ID,
                "id2label":     ID2LABEL,
                "train_samples": len(train_df),
                "val_samples":   len(val_df),
                "eval_accuracy": eval_metrics.get("eval_accuracy"),
                "eval_f1_macro": eval_metrics.get("eval_f1_macro"),
                "epochs":        epochs,
                "lora_r":        lora_r,
                "lora_alpha":    lora_alpha,
            },
            f,
            indent=2,
        )

    logger.info(
        f"\n[OK] Fine-tuning done!\n"
        f"  Adapter saved : {out_path}\n"
        f"  Accuracy      : {eval_metrics.get('eval_accuracy', 'N/A'):.4f}\n"
        f"  F1 (macro)    : {eval_metrics.get('eval_f1_macro', 'N/A'):.4f}\n"
    )
    return str(out_path)


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="QLoRA fine-tune RoBERTa sentiment model")
    parser.add_argument("--output",     default=DEFAULT_OUT,  help="Output directory for LoRA adapter")
    parser.add_argument("--epochs",     type=int,   default=3,     help="Number of training epochs (default: 3)")
    parser.add_argument("--lr",         type=float, default=2e-4,  help="Learning rate (default: 2e-4)")
    parser.add_argument("--batch-size", type=int,   default=16,    help="Per-device batch size (default: 16)")
    parser.add_argument("--max-length", type=int,   default=128,   help="Max token length (default: 128)")
    parser.add_argument("--lora-r",     type=int,   default=16,    help="LoRA rank r (default: 16)")
    parser.add_argument("--lora-alpha", type=int,   default=32,    help="LoRA alpha (default: 32)")
    parser.add_argument("--val-split",  type=float, default=0.15,  help="Validation split fraction (default: 0.15)")
    parser.add_argument("--seed",       type=int,   default=42)
    args = parser.parse_args()

    finetune(
        output_dir=args.output,
        epochs=args.epochs,
        lr=args.lr,
        batch_size=args.batch_size,
        max_length=args.max_length,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        val_split=args.val_split,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
