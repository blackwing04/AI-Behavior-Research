"""
模型工具函數 - 統一管理模型載入、推理等操作

此模組現在作為 chat.py 的包裝，確保 UI 和其他工具使用一致的實現。
所有聊天相關邏輯都集中在 chat.py 模組中。
"""
from pathlib import Path
import sys

# 確保能找到 chat 模組
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

# 直接從 chat 模組導入公共接口
from chat import (
    load_chat_model, 
    chat_ask, 
    format_qwen_single_turn, 
    SYSTEM_PROMPTS,
)

# 取得專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 保留原有的導出接口，以便向後相容
__all__ = [
    "load_chat_model", 
    "chat_ask", 
    "format_qwen_single_turn", 
    "SYSTEM_PROMPTS",
    "PROJECT_ROOT"
]
