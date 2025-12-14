"""
聊天模塊 - 支持命令行和 UI 調用
可被 UI 直接導入使用，或作為獨立 CLI 工具運行
"""
import os
import sys
import torch
import argparse
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

# 動態獲取專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 多語言 system_prompt
SYSTEM_PROMPTS = {
    "en-US": (
        "You are a rational and stable AI that follows ethical principles, "
        "is capable of self-correction, and reasons according to E/I/M structure. "
        "You can have natural conversations while maintaining clarity and safety."
    ),
    "zh-TW": (
        "你是一個遵守五律、冷靜穩定、能自我修正並依照 E/I/M 推理的 AI。"
        "你可以自然對話，但始終保持清晰、安全。"
    ),
    "zh-CN": (
        "你是一个遵守五律、冷静稳定、能自我修正并依照 E/I/M 推理的 AI。"
        "你可以自然对话，但始终保持清晰、安全。"
    ),
}


def format_qwen_single_turn(user_msg: str, system_prompt: str) -> str:
    """
    格式化 Qwen 單輪對話提示
    
    Args:
        user_msg: 用戶訊息
        system_prompt: 系統提示
    
    Returns:
        格式化的提示文本
    """
    text = (
        "<|im_start|>system\n" + system_prompt + "\n<|im_end|>\n"
        + f"<|im_start|>user\n{user_msg}\n<|im_end|>\n"
        + "<|im_start|>assistant\n"
    )
    return text


def load_chat_model(base_model_path: str, lora_path: str = None):
    """
    載入聊天模型（基礎模型 + 可選 LoRA）
    
    Args:
        base_model_path: 基礎模型路徑
        lora_path: LoRA 適配器路徑（可選）
    
    Returns:
        (tokenizer, model) 或 (None, None) 如果失敗
    """
    try:
        print(f"📦 載入 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
        
        print(f"📦 載入基礎模型...")
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )
        
        # 如果提供了 LoRA 路徑，套用 LoRA
        if lora_path and Path(lora_path).exists():
            print(f"📦 套用 LoRA 適配器: {Path(lora_path).name}")
            model = PeftModel.from_pretrained(base_model, lora_path)
        else:
            print(f"📦 使用基礎模型（無 LoRA）")
            model = base_model
        
        model.eval()
        print(f"✅ 模型準備完成")
        return tokenizer, model
    except Exception as e:
        print(f"❌ 模型載入失敗：{str(e)}")
        return None, None


def chat_ask(tokenizer, model, user_msg: str, lang: str = "zh-TW") -> str:
    """
    執行聊天推理（Qwen 格式）
    
    Args:
        tokenizer: 分詞器
        model: 模型
        user_msg: 用戶訊息
        lang: 語言代碼（en-US / zh-TW / zh-CN），決定系統提示
    
    Returns:
        AI 回覆
    """
    # 驗證輸入
    if tokenizer is None or model is None:
        return "❌ 模型未加載，請先點擊 'Load Model' 按鈕。"
    
    if not user_msg or not user_msg.strip():
        return "❌ 請輸入消息。"
    
    try:
        # 根據語言選擇系統提示
        if not isinstance(lang, str):
            lang = "zh-TW"
        
        if lang not in SYSTEM_PROMPTS:
            lang = "zh-TW"
        
        system_prompt = SYSTEM_PROMPTS.get(lang, SYSTEM_PROMPTS["zh-TW"])
        
        prompt = format_qwen_single_turn(user_msg, system_prompt)
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=300,
                do_sample=False,
                temperature=0.7,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.eos_token_id,
            )
        
        decoded = tokenizer.decode(outputs[0], skip_special_tokens=False)
        
        # 只提取最後的 assistant 部分（跳過 system 和 user）
        if "<|im_start|>assistant" in decoded:
            # 取最後一個 assistant 之後的部分（確保只有 assistant 回應）
            answer = decoded.split("<|im_start|>assistant")[-1]
        else:
            answer = decoded
        
        # 移除 <|im_end|> 及其之後的所有內容
        if "<|im_end|>" in answer:
            answer = answer.split("<|im_end|>")[0]
        
        # 清理所有特殊標記
        special_tokens = [
            "<|endoftext|>",
            "<|im_end|>",
            "<|im_start|>",
            "<|system|>",
            "<|user|>",
            "<|assistant|>"
        ]
        for token in special_tokens:
            answer = answer.replace(token, "")
        
        # 最後 strip 移除前後空白
        answer = answer.strip()
        
        # 如果結果為空，返回提示信息
        if not answer:
            return "（無有效回應）"
        
        return answer
    except Exception as e:
        return f"❌ 推理失敗：{str(e)}"


def run_cli_interactive(base_model_path: str, lora_path: str = None, lang: str = "zh-TW"):
    """
    運行交互式命令行聊天
    
    Args:
        base_model_path: 基礎模型路徑
        lora_path: LoRA 適配器路徑（可選）
        lang: 語言代碼
    """
    tokenizer, model = load_chat_model(base_model_path, lora_path)
    
    if tokenizer is None or model is None:
        print("❌ 無法載入模型，退出")
        return
    
    print("\n" + "=" * 50)
    print(f"  聊天模式 - 語言: {lang}")
    print("=" * 50)
    print("輸入 'exit' 或 'quit' 離開\n")
    
    while True:
        msg = input("你：").strip()
        if msg in ["exit", "quit"]:
            print("再見！")
            break
        
        if not msg:
            continue
        
        reply = chat_ask(tokenizer, model, msg, lang)
        print(f"AI：{reply}\n")


# ========== CLI 入口 ==========
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="聊天模型 - 命令行交互式介面")
    parser.add_argument(
        "--model_path",
        type=str,
        default=str(PROJECT_ROOT / "models" / "qwen2.5-3b"),
        help="基礎模型路徑（預設: models/qwen2.5-3b）"
    )
    parser.add_argument(
        "--lora",
        type=str,
        default=None,
        help="LoRA 適配器路徑（可選）"
    )
    parser.add_argument(
        "--lang",
        type=str,
        choices=["en-US", "zh-TW", "zh-CN"],
        default="zh-TW",
        help="語言代碼（預設: zh-TW）"
    )
    
    args = parser.parse_args()
    
    # 驗證基礎模型路徑
    model_path = Path(args.model_path)
    if not model_path.exists():
        print(f"❌ 錯誤：基礎模型路徑不存在: {args.model_path}")
        sys.exit(1)
    
    # 驗證 LoRA 路徑（如果提供）
    lora_path = None
    if args.lora:
        lora_path = Path(args.lora)
        if not lora_path.exists():
            print(f"❌ 錯誤：LoRA 路徑不存在: {args.lora}")
            sys.exit(1)
    
    # 運行交互式聊天
    run_cli_interactive(str(model_path), str(lora_path) if lora_path else None, args.lang)
