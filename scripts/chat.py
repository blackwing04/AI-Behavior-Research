import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


BASE_MODEL = r"H:\AI-Behavior-Research\models\qwen2.5-3b"
LORA_PATH  = r"H:\AI-Behavior-Research\lora_output\V4\qwen25_behavior_v4.3"

SYSTEM_PROMPT = (
    "你是一個遵守五律、冷靜穩定、能自我修正並依照 E/I/M 推理的 AI。"
    "你可以自然對話，但始終保持清晰、安全。"
)

# ---- 會話記錄 ----
chat_history = [
    {"role": "system", "content": SYSTEM_PROMPT}
]


# ---- Qwen 官方格式 ----
def format_qwen_dialogue(history):
    text = "<|im_start|>system\n" + SYSTEM_PROMPT + "\n<|im_end|>\n"

    for msg in history:
        if msg["role"] == "user":
            text += f"<|im_start|>user\n{msg['content']}\n<|im_end|>\n"
        elif msg["role"] == "assistant":
            text += f"<|im_start|>assistant\n{msg['content']}\n<|im_end|>\n"

    # 🔥 最重要：assistant 開始生成的位置
    text += "<|im_start|>assistant\n"
    return text


print("🔄 載入 tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)

print("🔄 載入模型...")
base = AutoModelForCausalLM.from_pretrained(
    BASE_MODEL,
    torch_dtype=torch.bfloat16,
    device_map="auto",
    trust_remote_code=True,
)

print("🔄 套用 LoRA...")
model = PeftModel.from_pretrained(base, LORA_PATH)
model.eval()


def ask(msg):
    # 加到對話記錄
    chat_history.append({"role": "user", "content": msg})

    # 組 prompt
    prompt = format_qwen_dialogue(chat_history)

    # token 化
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    # 生成
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=300,
            do_sample=False,
            temperature=0.7,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.eos_token_id,
        )

    decoded = tokenizer.decode(output[0], skip_special_tokens=False)

    # 從最後一段 assistant 拿回答
    try:
        answer = decoded.split("<|im_start|>assistant")[-1]
        answer = answer.split("<|im_end|>")[0].strip()
    except:
        answer = decoded

    chat_history.append({"role": "assistant", "content": answer})
    return answer


# ---- CLI ----
print("\n====================================")
print(" 🧠 V3 Chat Model — Ready")
print("====================================")
print("輸入 exit 離開\n")

while True:
    msg = input("你：").strip()
    if msg in ["exit", "quit"]:
        print("再見！")
        break

    reply = ask(msg)
    print(f"AI：{reply}\n")
