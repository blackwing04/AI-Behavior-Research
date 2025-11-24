import json
import torch
from dataclasses import dataclass
from typing import Dict, List

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

# -------------------------------------------------------
# 路徑設定
# -------------------------------------------------------
BASE_MODEL = r"H:\AI-Behavior-Research\models\qwen2.5-3b"
DATASET_PATH = r"H:\AI-Behavior-Research\datasets\behavior_mix_dataset.jsonl"
OUTPUT_DIR = r"H:\AI-Behavior-Research\lora_output\V4\qwen25_behavior_v4.3"

# -------------------------------------------------------
# Qwen2.5 系統提示
# -------------------------------------------------------
SYSTEM_PROMPT = (
    "你是一個遵守五律、具備穩定人格、成熟推理、自我修正、"
    "並能依照 E/I/M 結構進行判斷的 AI。保持冷靜、清晰、穩定。"
    "在日常對話中，可以自然簡短地互動，但仍維持邏輯清晰和安全邊界。"
)

def qwen_chat_template(instruction: str, user_input: str, assistant_output: str) -> str:
    user_msg = (instruction.strip() + "\n" + user_input.strip()).strip()
    final_prompt = (
        "<|im_start|>system\n" +
        SYSTEM_PROMPT + "\n<|im_end|>\n"
        "<|im_start|>user\n" +
        user_msg + "\n<|im_end|>\n"
        "<|im_start|>assistant\n" +
        assistant_output.strip() + "\n<|im_end|>\n"
    )
    return final_prompt


# -------------------------------------------------------
# Dataset（含 label masking）
# -------------------------------------------------------
@dataclass
class SFTDataset:
    data: List[Dict]
    tokenizer: AutoTokenizer

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        ex = self.data[idx]

        prompt = qwen_chat_template(
            ex["instruction"],
            ex["input"],
            ex["output"]
        )

        # --- tokenize ---
        tokenized = self.tokenizer(
            prompt,
            truncation=True,
            max_length=1024,
            padding="max_length",
            return_tensors="pt",
        )

        input_ids = tokenized["input_ids"][0]
        attention_mask = tokenized["attention_mask"][0]

        # --- 建立 labels ---
        labels = input_ids.clone()

        # 將 <|im_start|>assistant 之前全部 mask (-100)
        assistant_token_id = self.tokenizer.encode("<|im_start|>assistant")[0]

        # 找到 assistant 的起始位置
        positions = (input_ids == assistant_token_id).nonzero(as_tuple=True)[0]

        if len(positions) > 0:
            start = positions[0]
        else:
            start = 0  # 萬一找不到，保底不訓練

        # mask（user/system）部分
        labels[:start] = -100

        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }


# -------------------------------------------------------
# 主程式
# -------------------------------------------------------
def main():
    print("🔄 載入 tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

    print("🔄 載入模型（4bit）...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_quant_type="nf4",
    )

    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        quantization_config=bnb_config,
        trust_remote_code=True,
    )

    print("🔧 準備 QLoRA 訓練...")
    model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=32,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # --- Dataset ---
    dataset_raw = []
    with open(DATASET_PATH, "r", encoding="utf-8-sig") as f:
        for line in f:
            if not line.strip():
                continue
            dataset_raw.append(json.loads(line))


    train_dataset = SFTDataset(dataset_raw, tokenizer)
    print(f"📄 資料集載入共 {len(train_dataset)} 筆")

    # --- Training Args ---
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=8,
        num_train_epochs=1,
        logging_steps=5,
        save_total_limit=2,
        learning_rate=2e-4,
        bf16=True,
        warmup_ratio=0.05,
        optim="paged_adamw_8bit",
        lr_scheduler_type="cosine",
    )

    print("🚀 開始訓練（含 Chat 模板 + Label Masking）...")
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
    )

    trainer.train()

    print("💾 儲存 LoRA...")
    model.save_pretrained(OUTPUT_DIR)
    print("🎉 訓練完成！")


if __name__ == "__main__":
    main()
