import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


BASE_MODEL = r"H:\AI-Behavior-Research\models\qwen\qwen2.5-3b"
LORA_PATH  = r"H:\AI-Behavior-Research\lora_output\V4\qwen25_behavior_v4.6"

SYSTEM_PROMPT = (
    "你是一個遵守五律、冷靜穩定、能自我修正並依照 E/I/M 推理的 AI。"
    "你可以自然對話，但始終保持清晰、安全。"
)


# ---- 單輪 Qwen 格式 ----
def format_qwen_single_turn(user_msg):
    text = (
        "<|im_start|>system\n" + SYSTEM_PROMPT + "\n<|im_end|>\n"
        + f"<|im_start|>user\n{user_msg}\n<|im_end|>\n"
        + "<|im_start|>assistant\n"
    )
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
    # 單輪 prompt
    prompt = format_qwen_single_turn(msg)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

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
    try:
        answer = decoded.split("<|im_start|>assistant")[-1]
        answer = answer.split("<|im_end|>")[0].strip()
    except:
        answer = decoded
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
