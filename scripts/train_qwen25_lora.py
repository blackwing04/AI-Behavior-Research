import json
import torch
import csv
from dataclasses import dataclass
from typing import Dict, List
from datetime import datetime
import os

from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    TrainerCallback,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training


# -------------------------------------------------------
# JSONL 驗證函數
# -------------------------------------------------------
def validate_jsonl(file_path: str) -> tuple[bool, str]:
    """
    驗證 JSONL 檔案格式
    
    Returns:
        (is_valid, message): (是否有效, 訊息)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📋 驗證 JSONL 檔案: {file_path}")
    print(f"   總行數: {len(lines)}")
    
    errors = []
    valid_count = 0
    
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        
        try:
            json.loads(line)
            valid_count += 1
        except json.JSONDecodeError as e:
            errors.append(f"第 {i} 行: {str(e)[:100]}")
    
    if errors:
        message = f"\n❌ 找到 {len(errors)} 個 JSON 格式錯誤:\n"
        for err in errors[:10]:
            message += f"   {err}\n"
        if len(errors) > 10:
            message += f"   ... 還有 {len(errors) - 10} 個錯誤\n"
        return False, message
    else:
        message = f"✅ JSONL 格式驗證通過！({valid_count} 筆有效資料)"
        return True, message


# -------------------------------------------------------
# 訓練指標記錄器
# -------------------------------------------------------
class MetricsLogger:
    """記錄訓練過程中的所有指標"""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.metrics_file = os.path.join(output_dir, "training_metrics.csv")
        self.metrics_list = []
        
        # 建立 CSV 標題
        os.makedirs(output_dir, exist_ok=True)
        with open(self.metrics_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['epoch', 'step', 'loss', 'grad_norm', 'learning_rate', 'timestamp'])
    
    def log_metrics(self, epoch: float, step: int, loss: float, grad_norm: float, lr: float):
        """記錄一條訓練指標"""
        record = {
            'epoch': epoch,
            'step': step,
            'loss': loss,
            'grad_norm': grad_norm,
            'learning_rate': lr,
            'timestamp': datetime.now().isoformat()
        }
        self.metrics_list.append(record)
        
        # 實時寫入 CSV
        with open(self.metrics_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([epoch, step, loss, grad_norm, lr, record['timestamp']])
    
    def save_json(self):
        """保存為 JSON 格式"""



# -------------------------------------------------------
# 自訂 Callback 來記錄訓練指標
# -------------------------------------------------------
class MetricsCallback(TrainerCallback):
    """在訓練過程中記錄梯度和損失"""
    
    def __init__(self, metrics_logger: MetricsLogger, model):
        self.metrics_logger = metrics_logger
        self.model = model
    

    def on_log(self, args, state, control, logs=None, **kwargs):
        """在 Trainer log 時記錄指標（此時 grad_norm 若有會被 log）"""
        if logs and 'loss' in logs:
            epoch = logs.get('epoch', state.epoch)
            step = state.global_step
            loss = logs.get('loss', 0)
            lr = logs.get('learning_rate', args.learning_rate)
            grad_norm = logs.get('grad_norm', 0.0)  # 若 Trainer 有 log grad_norm
            self.metrics_logger.log_metrics(epoch, step, loss, grad_norm, lr)
            if step % 10 == 0:
                print(f"Step {step} | Loss: {loss:.4f} | GN: {grad_norm:.4f} | Epoch: {epoch:.2f}")
    
    def _compute_grad_norm(self) -> float:
        """計算模型梯度的 L2 範數"""
        total_norm = 0.0
        for p in self.model.parameters():
            if p.grad is not None:
                total_norm += p.grad.data.norm(2).item() ** 2
        total_norm = total_norm ** 0.5
        return total_norm


# -------------------------------------------------------
# 路徑設定
# -------------------------------------------------------
# 選擇資料集來源：'behavior' 或 'copilot_generic'
DATASET_SOURCE = "behavior"  # ← 改這裡切換資料集

# 對應的輸出資料夾
OUTPUT_MAPPING = {
    "behavior": r"H:\AI-Behavior-Research\lora_output\V4\qwen25_behavior_v4.6",
    "copilot_generic": r"H:\AI-Behavior-Research\lora_output\copilot_generic",
}

BASE_MODEL = r"H:\AI-Behavior-Research\models\qwen\qwen2.5-3b_Test"

# 路徑選擇
if DATASET_SOURCE == "behavior":
    # V4.4: 基於 V4 的改進版本，整合本能方程式訓練（同樣在 V4 文件夾）
    DATASET_PATH = r"H:\AI-Behavior-Research\datasets\behavior\V4\behavior_dataset.jsonl"
elif DATASET_SOURCE == "copilot_generic":
    DATASET_PATH = r"H:\AI-Behavior-Research\datasets\copilot_generic\copilot_generic_dataset.jsonl"

OUTPUT_DIR = OUTPUT_MAPPING[DATASET_SOURCE]

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
    print("=" * 60)
    print("🔍 第一步：驗證資料集")
    print("=" * 60)
    
    # 驗證 JSONL 格式
    is_valid, validation_message = validate_jsonl(DATASET_PATH)
    print(validation_message)
    
    if not is_valid:
        print("\n⚠️  資料集格式有誤，請先修正後再訓練")
        return
    
    print("\n" + "=" * 60)
    print("🔄 第二步：載入模型與準備訓練")
    print("=" * 60)
    
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
    
    # 初始化指標記錄器
    metrics_logger = MetricsLogger(OUTPUT_DIR)
    
    # 自訂 Callback 來記錄訓練指標
    metrics_callback = MetricsCallback(metrics_logger, model)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        tokenizer=tokenizer,
        callbacks=[metrics_callback],
    )

    trainer.train()

    print("💾 儲存 LoRA...")
    model.save_pretrained(OUTPUT_DIR)
    
    # 保存訓練指標
    metrics_logger.save_json()
    
    print("🎉 訓練完成！")
    print(f"📊 訓練指標已保存到:")
    print(f"   - CSV: {metrics_logger.metrics_file}")
if __name__ == "__main__":
    main()
