import streamlit as st
import subprocess
import os
import sys
import threading
from pathlib import Path
from datetime import datetime
import json
import hashlib
import time

# 導入模型工具函數
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from model_utils import load_chat_model, chat_ask, format_qwen_single_turn

# ==============================
# 多語言配置 - 從獨立 JSON 檔案載入
# ==============================
TRANSLATE_DIR = Path(__file__).resolve().parent / "translate"

# 載入翻譯文件
def load_translations():
    """從 JSON 檔案載入翻譯"""
    translations = {}
    for lang_file in ["zh-TW.json", "zh-CN.json", "en-US.json"]:
        lang = lang_file.replace(".json", "")
        json_path = TRANSLATE_DIR / lang_file
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                translations[lang] = json.load(f)
        except Exception as e:
            print(f"⚠️ 無法載入翻譯文件 {lang_file}: {e}")
            translations[lang] = {}
    return translations

LANGUAGES = load_translations()

# 備用：如果載入失敗，顯示警告但不阻止啟動
if not LANGUAGES or not any(LANGUAGES.values()):
    print("⚠️ 翻譯系統載入失敗！請檢查 translate 目錄。")
    LANGUAGES = {"zh-TW": {}, "zh-CN": {}, "en-US": {}}

# ==============================
# 初始化 Session State
# ==============================
if "language" not in st.session_state:
    st.session_state.language = "zh-TW"

if "train_output" not in st.session_state:
    st.session_state.train_output = ""

if "test_output" not in st.session_state:
    st.session_state.test_output = ""

if "train_status" not in st.session_state:
    st.session_state.train_status = None  # None, "running", "success", "failed"

if "test_status" not in st.session_state:
    st.session_state.test_status = None

if "download_output" not in st.session_state:
    st.session_state.download_output = ""

if "download_status" not in st.session_state:
    st.session_state.download_status = None

if "is_downloading" not in st.session_state:
    st.session_state.is_downloading = False

if "is_training" not in st.session_state:
    st.session_state.is_training = False

if "is_testing" not in st.session_state:
    st.session_state.is_testing = False

if "hf_token" not in st.session_state:
    st.session_state.hf_token = ""

if "download_process" not in st.session_state:
    st.session_state.download_process = None

if "overwrite_download" not in st.session_state:
    st.session_state.overwrite_download = False

# ==============================
# HuggingFace Token 本地保存管理
# ==============================
CONFIG_DIR = Path(os.path.expanduser("~")) / ".ai_behavior_research"
HF_TOKEN_FILE = CONFIG_DIR / "hf_token.json"

def ensure_config_dir():
    """確保配置目錄存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def save_hf_token(token):
    """保存 HuggingFace Token 到本地"""
    ensure_config_dir()
    try:
        data = {
            "token": token,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(HF_TOKEN_FILE, 'w') as f:
            json.dump(data, f)
        return True
    except Exception as e:
        print(f"Error saving token: {e}")
        return False

def load_hf_token():
    """從本地讀取已保存的 HuggingFace Token"""
    try:
        if HF_TOKEN_FILE.exists():
            with open(HF_TOKEN_FILE, 'r') as f:
                data = json.load(f)
                # 返回實際 token
                return data.get("token")
        return None
    except Exception:
        return None

def clear_hf_token():
    """刪除已保存的 HuggingFace Token"""
    try:
        if HF_TOKEN_FILE.exists():
            os.remove(HF_TOKEN_FILE)
        return True
    except Exception:
        return False

# 啟動時嘗試載入已保存的 Token
saved_token = load_hf_token()
if saved_token and not st.session_state.hf_token:
    st.session_state.hf_token = saved_token

# 安全提示展開/收起狀態
if "security_notice_expanded" not in st.session_state:
    st.session_state.security_notice_expanded = True

# ==============================
# 取得翻譯文本
# ==============================
def get_text(key):
    return LANGUAGES[st.session_state.language].get(key, key)

# ==============================
# UI 佈局
# ==============================
st.set_page_config(
    page_title=get_text("title"), 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 設定全域字體大小和輸出容器
st.markdown("""
    <style>
    /* 放大標題 */
    h1, h2, h3 { font-size: 1.8rem !important; }
    /* 放大 Tab 文字 */
    [data-baseweb="tab-list"] button { font-size: 1.2rem !important; }
    /* 放大標籤 */
    label { font-size: 1.1rem !important; }
    /* 放大按鈕文字 */
    button { font-size: 1.1rem !important; }
    
    /* 輸出容器樣式 */
    .console-output {
        height: 600px;
        overflow-y: auto;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 12px;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    /* 聊天訊息容器 */
    .chat-container {
        height: 500px;
        overflow-y: auto;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        padding: 12px;
    }
    </style>
""", unsafe_allow_html=True)

# 頂部語言選擇
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.session_state.language = st.selectbox(
        get_text("lang_select"),
        ["zh-TW", "zh-CN", "en-US"],
        index=["zh-TW", "zh-CN", "en-US"].index(st.session_state.language),
        key="lang_select"
    )

st.title(get_text("title"))

# 安全提示展開/收起按鈕
col_toggle, col_space = st.columns([0.06, 0.94])
with col_toggle:
    if st.button(
        "🔒",
        key="toggle_security_notice",
        help="Click to toggle"
    ):
        st.session_state.security_notice_expanded = not st.session_state.security_notice_expanded

if st.session_state.security_notice_expanded:
    token_path = CONFIG_DIR / 'hf_token.json'
    st.info(
        f"""
        {get_text('security_notice_title')}
        
        **{get_text('security_token_location')}:**
        • 💾 {get_text('security_saved_at')}: `{token_path}`
        • {get_text('security_outside_project')}
        • {get_text('security_outside_sync')}
        
        **{get_text('security_token_safety')}:**
        • {get_text('security_env_variable')}
        • {get_text('security_filter_output')}
        • {get_text('security_no_sync_folder')}
        """,
        icon="🔒"
    )

st.divider()

# ==============================
# 取得專案根目錄路徑
# ==============================
# 從 ui_app.py 的位置往上找到專案根目錄
from pathlib import Path
# 自動偵測專案根目錄，不需硬寫磁碟機
current_file = Path(__file__).resolve()
ui_dir = current_file.parent  # H:\AI-Behavior-Research\scripts\ui
scripts_dir = ui_dir.parent    # H:\AI-Behavior-Research\scripts
PROJECT_ROOT = scripts_dir.parent  # H:\AI-Behavior-Research

# 確保路徑存在
if not (PROJECT_ROOT / "models").exists():
    print(f"⚠️ {get_text('warning_models_dir')} {PROJECT_ROOT}")

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATASETS_DIR = PROJECT_ROOT / "datasets"
LORA_OUTPUT_DIR = PROJECT_ROOT / "lora_output" / "qwen2.5-3b"
MODELS_DIR = PROJECT_ROOT / "models"

# 載入模型配置
MODELS_CONFIG_PATH = PROJECT_ROOT / "models_config.json"
if MODELS_CONFIG_PATH.exists():
    with open(MODELS_CONFIG_PATH, 'r', encoding='utf-8') as f:
        MODELS_CONFIG = json.load(f)
else:
    MODELS_CONFIG = {"models": []}

# 調試輸出（只在控制台顯示一次）
print(f"🖥️ {get_text('debug_project_root')} {PROJECT_ROOT}")
print(f"🖥️ {get_text('debug_models_dir')} {MODELS_DIR}")
print(f"🖥️ {get_text('debug_models_exist')} {MODELS_DIR.exists()}")

# ==============================
# Chat 模型載入（使用 Streamlit cache 包裝）
# ==============================
@st.cache_resource
def _load_chat_model_cached(base_model_path, lora_path):
    """包裝 load_chat_model 供 Streamlit cache 使用"""
    try:
        print(f"[UI] Loading model from: {base_model_path}")
        if lora_path:
            print(f"[UI] With LoRA: {lora_path}")
        tokenizer, model = load_chat_model(base_model_path, lora_path)
        if tokenizer is None or model is None:
            print(f"[UI] Model loading returned None")
            return None, None
        print(f"[UI] Model loaded successfully")
        return tokenizer, model
    except Exception as e:
        print(f"[UI] Error loading model: {str(e)}")
        import traceback
        traceback.print_exc()
        return None, None

# ==============================
# 過濾敏感信息（Token/密碼）
# ==============================
def filter_sensitive_output(text):
    """過濾輸出中的敏感信息（Token、密碼等）"""
    if not text:
        return text
    
    import re
    
    # 1. HuggingFace Token pattern: hf_xxxxx
    text = re.sub(r'hf_[A-Za-z0-9]{30,}', 'hf_****', text)
    
    # 2. API Key patterns
    text = re.sub(r'api[_-]?key[\s=:]+([S]+)', 'api_key=****', text, flags=re.IGNORECASE)
    text = re.sub(r'token[\s=:]+([S]+)', 'token=****', text, flags=re.IGNORECASE)
    
    # 3. 密碼模式
    text = re.sub(r'password[\s=:]+([S]+)', 'password=****', text, flags=re.IGNORECASE)
    
    # 4. Authorization header
    text = re.sub(r'authorization[\s=:]+Bearer\s+([S]+)', 'Authorization: Bearer ****', text, flags=re.IGNORECASE)
    
    return text

# ==============================
# 執行命令並串流輸出
# ==============================
def run_command_with_output(command, output_placeholder, filter_output=True):
    """執行命令並即時顯示輸出"""
    try:
        # 使用 PowerShell 執行（Windows 環境）
        process = subprocess.Popen(
            ["powershell", "-Command", command],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=str(PROJECT_ROOT)
        )
        
        output_text = ""
        for line in process.stdout:
            line = line.rstrip()
            # 過濾敏感信息
            if filter_output:
                line = filter_sensitive_output(line)
            output_text += line + "\n"
            # 即時更新 UI - 使用自定義容器
            with output_placeholder.container():
                st.markdown(
                    f'<div class="console-output">{output_text.replace("<", "&lt;").replace(">", "&gt;")}</div>',
                    unsafe_allow_html=True
                )
        
        process.wait()
        return process.returncode, output_text
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        output_placeholder.error(error_msg)
        return 1, error_msg

# ==============================
# 下載模型函數
# ==============================
# ==============================
# 清理下載目錄函數
# ==============================
def cleanup_download_dir(local_dir):
    """清理未完成的下載目錄和 .cache 文件夾"""
    try:
        target_path = MODELS_DIR / local_dir
        cache_path = MODELS_DIR / f"{local_dir}.cache"
        
        # 嘗試刪除目標目錄
        if target_path.exists():
            try:
                import shutil
                # 強制刪除，即使文件被占用
                shutil.rmtree(str(target_path), ignore_errors=True)
                
                # 如果刪除失敗，嘗試清空目錄內容
                if target_path.exists():
                    for item in target_path.iterdir():
                        try:
                            if item.is_dir():
                                shutil.rmtree(str(item), ignore_errors=True)
                            else:
                                item.unlink()
                        except:
                            pass
            except:
                pass
        
        # 嘗試刪除 .cache 目錄
        if cache_path.exists():
            try:
                import shutil
                shutil.rmtree(str(cache_path), ignore_errors=True)
                
                # 如果刪除失敗，嘗試清空
                if cache_path.exists():
                    for item in cache_path.iterdir():
                        try:
                            if item.is_dir():
                                shutil.rmtree(str(item), ignore_errors=True)
                            else:
                                item.unlink()
                        except:
                            pass
            except:
                pass
        
        return True
    except Exception as e:
        print(f"清理失敗: {str(e)}")
        return False

def download_model(model_id, local_dir, hf_token=None, progress_callback=None, process_state=None):
    """下載 HuggingFace 模型（使用命令列工具以支援進度顯示，完整錯誤捕捉）"""
    output_text = ""
    process = None
    
    def filter_sensitive_info(text, token=None):
        """過濾敏感信息（如 Token）以防止暴露"""
        if token:
            # 遮蔽 Token（保留前 4 個字符和最後 4 個字符）
            masked_token = token[:4] + "*" * (len(token) - 8) + token[-4:] if len(token) > 8 else "****"
            text = text.replace(token, masked_token)
        # 使用通用過濾函數再過一次
        text = filter_sensitive_output(text)
        return text
    
    try:
        # 建立完整的目標路徑
        target_path = str(MODELS_DIR / local_dir)
        cache_path = str(MODELS_DIR / f"{local_dir}.cache")
        
        # 開始前清理舊的鎖定文件和 .cache 目錄（如果存在）
        import shutil
        lock_files = []
        try:
            # 查找並清理 .cache 目錄下的 .lock 文件
            cache_path_obj = MODELS_DIR / f"{local_dir}.cache"
            if cache_path_obj.exists():
                for lock_file in cache_path_obj.rglob("*.lock"):
                    try:
                        lock_file.unlink()
                        lock_files.append(str(lock_file))
                    except:
                        pass
            
            # 如果 .cache 目錄完全空了，刪除它
            if cache_path_obj.exists() and not any(cache_path_obj.rglob("*")):
                try:
                    shutil.rmtree(str(cache_path_obj), ignore_errors=True)
                except:
                    pass
        except Exception as e:
            print(f"清理鎖定文件時出錯: {e}")
        
        # 建立目標目錄（如果目錄已存在，hf download 會覆蓋）
        os.makedirs(MODELS_DIR, exist_ok=True)
        
        output_text = f"{get_text('download_start')}\n"
        output_text += f"{get_text('download_model_id')} {model_id}\n"
        output_text += f"{get_text('download_target_path')} {target_path}\n"
        
        # 顯示清理信息
        if lock_files:
            output_text += f"[清理] 已清理 {len(lock_files)} 個鎖定文件\n"
        
        output_text += "\n"
        output_text += f"{get_text('download_connecting')}\n"
        if progress_callback:
            progress_callback(output_text)
        
        # 設定環境變數
        env = os.environ.copy()
        if hf_token:
            env["HF_TOKEN"] = hf_token
        
        # 使用 hf download（比舊版更新更快）
        # 注意：hf download 不支持 --local-dir-use-symlinks 參數
        # 使用環境變數傳入 Token 而非命令列參數，避免在日誌中暴露
        cmd = f'hf download "{model_id}" --local-dir "{target_path}"'
        
        output_text += f"{get_text('download_start_files')}\n"
        if progress_callback:
            progress_callback(output_text)
        
        # 執行下載命令（使用非緩衝模式以確保實時輸出）
        # Token 通過環境變數傳入，不會暴露在命令列或輸出中
        process = subprocess.Popen(
            ["powershell", "-Command", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合併 stderr 到 stdout
            universal_newlines=True,
            cwd=str(PROJECT_ROOT),
            env=env,
            bufsize=0  # 完全非緩衝
        )
        
        # 保存進程引用到 session_state 以便取消時使用
        if process_state is not None:
            process_state["download_process"] = process
        
        # 設定信號處理，當按 Ctrl+C 或進程被終止時清理鎖定文件
        import signal
        def cleanup_on_interrupt(signum, frame):
            """中斷時的清理函數"""
            output_text = "\n[中止] 用戶中止了下載\n[清理] 正在清理鎖定文件...\n"
            try:
                cache_path_obj = MODELS_DIR / f"{local_dir}.cache"
                if cache_path_obj.exists():
                    for lock_file in cache_path_obj.rglob("*.lock"):
                        try:
                            lock_file.unlink()
                        except:
                            pass
                output_text += "[清理] 鎖定文件已清理\n"
            except:
                pass
            if progress_callback:
                progress_callback(output_text)
            raise KeyboardInterrupt()
        
        # 即時讀取輸出
        # 讀取標準輸出（過濾敏感信息）
        while True:
            line = process.stdout.readline()
            if not line:
                # 檢查進程是否已結束
                if process.poll() is not None:
                    break
                import time
                time.sleep(0.1)  # 短暫等待，再試一次
                continue
            
            line = line.rstrip()
            if line:
                # 過濾敏感信息
                line = filter_sensitive_info(line, hf_token)
                output_text += line + "\n"
                if progress_callback:
                    progress_callback(output_text)
        
        # 等待進程結束
        process.wait()
        
        # 檢查返回碼
        # 最終過濾敏感信息
        output_text = filter_sensitive_info(output_text, hf_token)
        
        if process.returncode == 0:
            output_text += f"\n{get_text('download_success_msg')}\n"
            output_text += f"{get_text('download_success_path')} {target_path}\n"
            if progress_callback:
                progress_callback(output_text)
            return 0, output_text
        else:
            output_text += f"\n{get_text('download_failed_msg')}\n"
            output_text += f"{get_text('download_return_code')} {process.returncode}\n"
            
            # 檢查常見錯誤
            if "401" in output_text or "Unauthorized" in output_text:
                output_text += f"{get_text('download_auth_failed')}\n"
            if "404" in output_text or "not found" in output_text.lower():
                output_text += f"{get_text('download_model_not_found')}\n"
            if "Connection" in output_text or "timeout" in output_text.lower():
                output_text += f"{get_text('download_connection_failed')}\n"
            
            if progress_callback:
                progress_callback(output_text)
            return process.returncode, output_text
            
    except FileNotFoundError as e:
        error_msg = f"{get_text('download_command_not_found')}\n"
        error_msg += f"{get_text('download_install_hint')}\n"
        error_msg += f"{get_text('download_error_detail')} {str(e)}\n"
        output_text += error_msg
        if progress_callback:
            progress_callback(output_text)
        return 1, output_text
    except Exception as e:
        error_msg = f"{get_text('download_exception')} {str(e)}\n"
        error_msg += f"{get_text('download_error_type')} {type(e).__name__}\n"
        output_text += error_msg
        if progress_callback:
            progress_callback(output_text)
        return 1, output_text

# ==============================
# 初始化 Chat Session State
if "chat_tokenizer" not in st.session_state:
    st.session_state.chat_tokenizer = None
if "chat_model" not in st.session_state:
    st.session_state.chat_model = None
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# ==============================
# Tab 1: 下載 / Tab 2: 訓練 / Tab 3: 測試 / Tab 4: 聊天 / Tab 5: 資料轉換
# ==============================
tab_download, tab_train, tab_test, tab_chat, tab_convert = st.tabs([
    f"📥 {get_text('download_title')}",
    f"🎓 {get_text('tab_train')}", 
    f"🧪 {get_text('tab_test')}", 
    f"💬 {get_text('chat_title')}",
    f"🔄 {get_text('convert_title')}"
])

with tab_train:
    st.header(get_text("train_title"))
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 選擇基礎模型
        train_base_models = []
        if MODELS_DIR.exists():
            train_base_models = [d.name for d in MODELS_DIR.iterdir() if d.is_dir()]
        
        if not train_base_models:
            st.error(get_text("no_model_found"))
            train_base_model = None
        else:
            train_base_model = st.selectbox(
                get_text("chat_base_model"),
                train_base_models,
                key="train_base_model_select"
            )
    
    with col2:
        train_lang = st.selectbox(
            get_text("train_lang"),
            ["en-US", "zh-TW", "zh-CN"],
            key="train_lang_select"
        )
    
    with col3:
        # 取得訓練版本目錄列表（v1, v2, v3, v4 等）
        train_versions = []
        dataset_lang_base = DATASETS_DIR / "behavior" / train_lang
        if dataset_lang_base.exists():
            train_versions = sorted([d.name for d in dataset_lang_base.iterdir() if d.is_dir()])
        
        if not train_versions:
            st.warning(f"⚠️ {get_text('warning_not_found_version').format(lang=train_lang)}")
            train_version = None
        else:
            train_version = st.selectbox(
                get_text("train_version"),
                train_versions,
                key="train_version_select"
            )
    
    # 第二行：選擇資料集檔案
    if train_version:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 根據選定的版本，取得該目錄下的所有 .jsonl 檔案
            train_datasets = []
            dataset_version_dir = DATASETS_DIR / "behavior" / train_lang / train_version
            if dataset_version_dir.exists():
                train_datasets = sorted([f.name for f in dataset_version_dir.glob("*.jsonl")])
            
            if not train_datasets:
                st.warning(f"⚠️ {get_text('warning_not_found_jsonl').format(version=train_version)}")
                train_dataset = None
            else:
                train_dataset = st.selectbox(
                    get_text("select_train_dataset"),
                    train_datasets,
                    key="train_dataset_select"
                )
        
        with col2:
            # 自訂版本標籤輸入框
            train_custom_version = st.text_input(
                get_text("train_custom_version"),
                value="",
                placeholder="e.g., v4.6_custom",
                key="train_custom_version_input"
            )
    else:
        train_dataset = None
        train_custom_version = ""
    
    # 決定最終使用的版本標籤
    final_train_version = train_custom_version.strip() if train_custom_version.strip() else train_version
    
    # 檢查輸出目錄是否存在
    train_output_dir = None
    train_output_exists = False
    if train_version and train_base_model:
        lang_suffix = train_lang.replace('-', '')
        model_name = train_base_model
        train_output_dir = LORA_OUTPUT_DIR / train_lang / final_train_version / f"qwen25_behavior_{final_train_version}_{lang_suffix}"
        train_output_exists = train_output_dir.exists()
    
    if train_output_exists:
        st.warning(f"⚠️ {get_text('warning_train_output_exists')}")
    
    col_train_btn1, col_train_btn2 = st.columns([1, 1])
    
    with col_train_btn1:
        train_disabled = st.session_state.is_training
        train_btn_label = get_text("train_btn_overwrite") if train_output_exists else get_text("train_btn")
        if st.button(
            train_btn_label, 
            key="train_start_btn", 
            type="primary",
            disabled=train_disabled
        ):
            if not train_version or not train_base_model or not train_dataset:
                st.error(get_text("error_msg"))
            else:
                # 清空之前的訓練輸出
                st.session_state.train_output = ""
                st.session_state.train_status = None
                st.session_state.is_training = True
                st.rerun()
    
    with col_train_btn2:
        if st.session_state.is_training:
            if st.button(get_text("cancel_train"), key="cancel_train_btn", type="secondary"):
                st.session_state.is_training = False
                st.session_state.train_status = "cancelled"
                # 添加取消訊息到輸出
                st.session_state.train_output = f"[{get_text('cancel')}] {get_text('train_cancelled')}\n"
                st.warning(f"⚠️ {get_text('train_cancelled')}")
                st.rerun()
    
    # 執行訓練
    if st.session_state.is_training:
        if not train_version or not train_base_model or not train_dataset:
            st.error(get_text("error_msg"))
            st.session_state.is_training = False
        else:
            st.session_state.train_status = "running"
            st.session_state.train_output = ""
            
            # 構建訓練命令
            train_script = str(SCRIPTS_DIR / "train_lora.py")
            base_model_path = str(MODELS_DIR / train_base_model)
            
            # 根據選定的版本和檔案，構建完整路徑
            dataset_file = str(DATASETS_DIR / "behavior" / train_lang / train_version / train_dataset)
            
            # 如果有自訂版本標籤，使用自訂版本；否則使用預設版本
            version_param = final_train_version if train_custom_version.strip() else train_version
            command = f"python \"{train_script}\" --lang {train_lang} --model_path \"{base_model_path}\" --dataset_version {version_param} --dataset_file \"{dataset_file}\""
            
            try:
                st.info(f"{get_text('train_running')}\n{get_text('command_label')}{command}")
                
                output_placeholder = st.empty()
                returncode, output = run_command_with_output(command, output_placeholder)
                
                st.session_state.train_output = output
                
                if returncode == 0:
                    st.session_state.train_status = "success"
                    st.success(get_text("train_success"))
                else:
                    st.session_state.train_status = "failed"
                    st.error(get_text("train_failed"))
            finally:
                st.session_state.is_training = False
                st.rerun()
    
    # 顯示訓練輸出
    if st.session_state.train_output:
        st.subheader(get_text("train_console"))
        # 使用自定義容器，設定固定高度和滾動
        st.markdown(
            f'<div class="console-output" id="train-console">{st.session_state.train_output.replace("<", "&lt;").replace(">", "&gt;")}</div>',
            unsafe_allow_html=True
        )
        # 自動滾動到底部（持續監聽內容變化）
        st.markdown("""
            <script>
            function scrollConsoleToBottom(elementId) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.scrollTop = element.scrollHeight;
                    const observer = new MutationObserver(() => {
                        element.scrollTop = element.scrollHeight;
                    });
                    observer.observe(element, {
                        childList: true,
                        subtree: true,
                        characterData: true
                    });
                }
            }
            scrollConsoleToBottom('train-console');
            setInterval(() => {
                const element = document.getElementById('train-console');
                if (element) {
                    element.scrollTop = element.scrollHeight;
                }
            }, 200);
            </script>
        """, unsafe_allow_html=True)

# ==============================
# Tab 2: 測試
# ==============================
with tab_test:
    st.header(get_text("test_title"))
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # 選擇基礎模型
        test_base_models = []
        if MODELS_DIR.exists():
            test_base_models = [d.name for d in MODELS_DIR.iterdir() if d.is_dir()]
        
        if not test_base_models:
            st.error(get_text("no_model_found"))
            test_base_model = None
        else:
            test_base_model = st.selectbox(
                get_text("chat_base_model"),
                test_base_models,
                key="test_base_model_select"
            )
    
    with col2:
        test_lang = st.selectbox(
            get_text("test_lang"),
            ["en-US", "zh-TW", "zh-CN"],
            key="test_lang_select"
        )
    
    with col3:
        # 取得該語言的 LoRA 模型目錄列表，加上「Base Model Only」選項
        # 結構：lora_output / model_name / lang / version / model_dir
        lora_dirs = [get_text("base_model_only")]  # 預設加入 base 選項
        if test_base_model:
            test_lora_dir = PROJECT_ROOT / "lora_output" / test_base_model / test_lang
            if test_lora_dir.exists():
                # 遞歸查找所有版本目錄下的模型目錄
                for version_dir in test_lora_dir.iterdir():
                    if version_dir.is_dir():
                        for model_dir in version_dir.iterdir():
                            if model_dir.is_dir():
                                lora_dirs.append(model_dir.name)
                lora_dirs = sorted(set(lora_dirs))  # 去重並排序
        
        test_lora = st.selectbox(
            get_text("test_lora"),
            lora_dirs,
            key="test_lora_select"
        )
    
    with col4:
        # 取得測試資料集列表
        test_datasets = []
        test_dataset_dir = DATASETS_DIR / "test" / test_lang
        if test_dataset_dir.exists():
            test_datasets = [f.name for f in test_dataset_dir.glob("*.jsonl")]
        
        if not test_datasets:
            st.warning(f"⚠️ {get_text('warning_not_found_test_datasets').format(lang=test_lang)}")
            test_dataset = None
        else:
            test_dataset = st.selectbox(
                get_text("test_dataset"),
                test_datasets,
                key="test_dataset_select"
            )
    
    # 檢查測試輸出目錄是否已存在
    test_output_dir = Path(PROJECT_ROOT) / "test_logs" / test_lang / test_lora if test_lora and test_lora != get_text("base_model_only") else None
    if not test_lora or test_lora == get_text("base_model_only"):
        test_output_dir = Path(PROJECT_ROOT) / "test_logs" / test_lang / "base_model"
    
    test_dir_exists = test_output_dir and test_output_dir.exists() and len(list(test_output_dir.iterdir())) > 0
    
    col_test_btn1, col_test_btn2 = st.columns([1, 1])
    
    with col_test_btn1:
        test_disabled = st.session_state.is_testing
        # 根據目錄是否存在改變按鈕文字
        test_btn_label = get_text("test_btn_rerun_overwrite") if test_dir_exists else get_text("test_btn")
        
        if st.button(
            test_btn_label, 
            key="test_start_btn", 
            type="primary",
            disabled=test_disabled
        ):
            if not test_lora or not test_dataset or not test_base_model:
                st.error(get_text("error_msg"))
            else:
                # 清空之前的測試輸出
                st.session_state.test_output = ""
                st.session_state.test_status = None
                st.session_state.is_testing = True
                st.rerun()
    
    with col_test_btn2:
        if st.session_state.is_testing:
            if st.button(get_text("cancel_test"), key="cancel_test_btn", type="secondary"):
                st.session_state.is_testing = False
                st.session_state.test_status = "cancelled"
                # 添加取消訊息到輸出
                st.session_state.test_output = f"[{get_text('cancel')}] {get_text('test_cancelled')}\n"
                st.warning(f"⚠️ {get_text('test_cancelled')}")
                st.rerun()
    
    # 顯示警告（如果目錄存在）
    if test_dir_exists:
        st.warning(f"⚠️ {get_text('warning_test_results_exist')}")
    
    # 執行測試
    if st.session_state.is_testing:
        if not test_lora or not test_dataset or not test_base_model:
            st.error(get_text("error_msg"))
            st.session_state.is_testing = False
        else:
            st.session_state.test_status = "running"
            st.session_state.test_output = ""
            
            base_model_path = str(MODELS_DIR / test_base_model)
            
            # 根據選擇決定使用哪個測試腳本
            test_dataset_file = str(DATASETS_DIR / "test" / test_lang / test_dataset)
            
            if test_lora == "base":
                # 使用 Base Model Only 測試
                test_script = str(SCRIPTS_DIR / "test_base_model.py")
                command = f"python \"{test_script}\" --lang {test_lang} --model_path \"{base_model_path}\" --test_file \"{test_dataset_file}\""
            else:
                # 使用 LoRA 測試
                test_script = str(SCRIPTS_DIR / "test_behavior.py")
                # 遞歸查找完整的 LoRA 路徑
                lora_path = None
                test_lora_base = PROJECT_ROOT / "lora_output" / test_base_model / test_lang
                for version_dir in test_lora_base.rglob("*"):
                    if version_dir.is_dir() and version_dir.name == test_lora:
                        lora_path = str(version_dir)
                        break
                
                if lora_path:
                    command = f"python \"{test_script}\" --lang {test_lang} --model_path \"{base_model_path}\" --lora \"{lora_path}\" --test_file \"{test_dataset_file}\""
                else:
                    st.error(f"無法找到 LoRA 模型: {test_lora}")
                    st.session_state.is_testing = False
            
            try:
                st.info(f"{get_text('test_running')}\n{get_text('command_label')}{command}")
                
                output_placeholder = st.empty()
                returncode, output = run_command_with_output(command, output_placeholder)
                
                st.session_state.test_output = output
                
                if returncode == 0:
                    st.session_state.test_status = "success"
                    st.success(get_text("test_success"))
                else:
                    st.session_state.test_status = "failed"
                    st.error(get_text("test_failed"))
            finally:
                st.session_state.is_testing = False
                st.rerun()
    
    # 顯示測試輸出
    if st.session_state.test_output:
        st.subheader(get_text("test_console"))
        # 使用自定義容器，設定固定高度和滾動
        st.markdown(
            f'<div class="console-output" id="test-console">{st.session_state.test_output.replace("<", "&lt;").replace(">", "&gt;")}</div>',
            unsafe_allow_html=True
        )
        # 自動滾動到底部（持續監聽內容變化）
        st.markdown("""
            <script>
            function scrollConsoleToBottom(elementId) {
                const element = document.getElementById(elementId);
                if (element) {
                    element.scrollTop = element.scrollHeight;
                    const observer = new MutationObserver(() => {
                        element.scrollTop = element.scrollHeight;
                    });
                    observer.observe(element, {
                        childList: true,
                        subtree: true,
                        characterData: true
                    });
                }
            }
            scrollConsoleToBottom('test-console');
            setInterval(() => {
                const element = document.getElementById('test-console');
                if (element) {
                    element.scrollTop = element.scrollHeight;
                }
            }, 200);
            </script>
        """, unsafe_allow_html=True)

# ==============================
# Tab 3: 聊天
# ==============================
with tab_chat:
    st.header(get_text("chat_title"))
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 取得基礎模型列表
        base_models = []
        if MODELS_DIR.exists():
            base_models = [d.name for d in MODELS_DIR.iterdir() if d.is_dir()]
        
        if base_models:
            chat_base = st.selectbox(
                get_text("chat_base_model"),
                base_models,
                key="chat_base_select"
            )
        else:
            st.error(get_text("no_model_found"))
            chat_base = None
    
    with col2:
        # 取得 LoRA 模型列表
        lora_models = [get_text("base_model_only")]
        
        chat_lang = st.selectbox(
            get_text("chat_lora_model"),
            ["en-US", "zh-TW", "zh-CN"],
            key="chat_lang_select"
        )
        # 保存到 session_state 以便在聊天時使用
        st.session_state.chat_lang = chat_lang
        
        # 根據選擇的基礎模型查找 LoRA 模型
        if chat_base:
            chat_lora_dir = PROJECT_ROOT / "lora_output" / chat_base / chat_lang
            if chat_lora_dir.exists():
                # 遞歸查找所有版本目錄下的模型目錄
                for version_dir in chat_lora_dir.iterdir():
                    if version_dir.is_dir():
                        for model_dir in version_dir.iterdir():
                            if model_dir.is_dir():
                                lora_models.append(model_dir.name)
                lora_models = sorted(set(lora_models))  # 去重並排序
        
        chat_lora = st.selectbox(
            get_text("lora_model_label"),
            lora_models,
            key="chat_lora_select"
        )
    
    # 載入模型按鈕
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button(get_text("chat_load_btn"), type="primary", key="chat_load_btn"):
            if chat_base:
                with st.spinner(get_text("chat_loading")):
                    base_path = str(MODELS_DIR / chat_base)
                    lora_path = None
                    
                    if chat_lora != get_text("base_model_only"):
                        # 遞歸查找模型目錄
                        chat_lora_base = PROJECT_ROOT / "lora_output" / chat_base / chat_lang
                        for version_dir in chat_lora_base.rglob("*"):
                            if version_dir.is_dir() and version_dir.name == chat_lora:
                                lora_path = str(version_dir)
                                break
                    
                    tokenizer, model = _load_chat_model_cached(base_path, lora_path)
                    
                    if tokenizer and model:
                        st.session_state.chat_tokenizer = tokenizer
                        st.session_state.chat_model = model
                        # 清除舊的聊天歷史
                        st.session_state.chat_messages = []
                        st.success(get_text("chat_loaded"))
                    else:
                        st.error(get_text("error_msg"))
    
    # 聊天界面
    if st.session_state.chat_model is not None:
        st.divider()
        st.subheader(get_text("chat_history"))
        
        # chat_ask 已經返回干淨的內容，直接使用
        def clean_response(text):
            """直接返回文本（chat_ask 已處理過）"""
            return text if text else ""
        
        # 顯示聊天記錄（使用自定義容器，自動滾動到底部）
        chat_html = '<div class="chat-container" id="chat-container">'
        for msg in st.session_state.chat_messages:
            # 清理特殊標記
            content = clean_response(msg["content"])
            if msg["role"] == "user":
                chat_html += f'<div style="margin: 8px 0; text-align: right;"><div style="display: inline-block; background-color: #e3f2fd; padding: 8px 12px; border-radius: 8px; max-width: 70%;"><strong>You:</strong> {content.replace("<", "&lt;").replace(">", "&gt;")}</div></div>'
            else:
                chat_html += f'<div style="margin: 8px 0;"><div style="display: inline-block; background-color: #f5f5f5; padding: 8px 12px; border-radius: 8px; max-width: 70%;"><strong>AI:</strong> {content.replace("<", "&lt;").replace(">", "&gt;")}</div></div>'
        chat_html += '</div>'
        
        st.markdown(chat_html, unsafe_allow_html=True)
        
        # 自動滾動到底部
        st.markdown("""
            <script>
            var chatContainer = document.getElementById('chat-container');
            if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
            </script>
        """, unsafe_allow_html=True)
        
        # 初始化聊天提交狀態
        if "chat_submitted" not in st.session_state:
            st.session_state.chat_submitted = False
        
        # 輸入框
        user_input = st.text_input(get_text("chat_input"), key="chat_input_field")
        # 發送按鈕
        chat_submit_btn = st.button(get_text("chat_send"), type="primary", key="chat_submit_btn", use_container_width=True)
        
        # 只在按鈕點擊且輸入不為空時提交
        if chat_submit_btn and user_input.strip():
            try:
                # 檢查模型是否已加載
                if st.session_state.chat_tokenizer is None or st.session_state.chat_model is None:
                    st.error(get_text("error_msg") + " - Model not loaded. Please click 'Load Model' first.")
                else:
                    # 添加用戶消息
                    st.session_state.chat_messages.append({"role": "user", "content": user_input})
                    
                    # AI 回覆
                    with st.spinner(get_text("chat_sending")):
                        # 確保獲取正確的語言值
                        chat_lang = st.session_state.get("chat_lang", "zh-TW")
                        if not chat_lang:
                            chat_lang = "zh-TW"
                        
                        ai_response = chat_ask(
                            st.session_state.chat_tokenizer,
                            st.session_state.chat_model,
                            user_input,
                            chat_lang
                        )
                        st.session_state.chat_messages.append({"role": "assistant", "content": ai_response})
                    
                    # 重新運行以更新聊天記錄（會自動滾動）
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Chat Error: {str(e)}")
                import traceback
                print(f"[UI] Chat Error Traceback:\n{traceback.format_exc()}")
    else:
        st.info(" " + get_text("chat_load_btn"))

# ==============================
# Tab 4: 模型下載
# ==============================
with tab_download:
    st.header(get_text("download_title"))
    
    # 品牌選擇
    col1, col2 = st.columns(2)
    
    with col1:
        brands = [model_brand["brand"] for model_brand in MODELS_CONFIG.get("models", [])]
        if brands:
            selected_brand = st.selectbox(
                get_text("download_brand"),
                brands,
                key="download_brand_select"
            )
        else:
            st.error(get_text("no_brand_found"))
            selected_brand = None
    
    # 規格選擇
    selected_model = None
    if selected_brand:
        with col2:
            # 根據品牌取得模型列表
            brand_models = None
            for item in MODELS_CONFIG.get("models", []):
                if item["brand"] == selected_brand:
                    brand_models = item["models"]
                    break
            
            if brand_models:
                model_names = [m["name"] for m in brand_models]
                selected_model_name = st.selectbox(
                    get_text("download_model"),
                    model_names,
                    key="download_model_select"
                )
                # 取得完整的模型信息
                for m in brand_models:
                    if m["name"] == selected_model_name:
                        selected_model = m
                        break
    
    # 顯示模型信息
    if selected_model:
        st.info(f"{get_text('model_description')} {selected_model['description']} | {get_text('model_size')} {selected_model['size']}")
    
    # HuggingFace 認證
    st.divider()
    st.subheader(get_text("download_hf_login"))
    
    # 檢查是否已有保存的 Token
    saved_token = load_hf_token()
    has_saved_token = saved_token is not None
    
    if "show_token_input" not in st.session_state:
        st.session_state.show_token_input = False
    
    if has_saved_token and not st.session_state.show_token_input:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success(get_text('token_saved_msg'))
        with col2:
            if st.button(get_text('reset_token_btn'), key="reset_token_btn"):
                clear_hf_token()
                st.session_state.hf_token = ""
                st.rerun()
        with col3:
            if st.button(get_text('change_token_btn'), key="change_token_btn"):
                st.session_state.show_token_input = True
                st.rerun()
    
    # 顯示 Token 輸入欄位（首次或用戶要求變更時）
    if not has_saved_token or st.session_state.show_token_input:
        col1, col2 = st.columns([3, 1])
        with col1:
            hf_token_input = st.text_input(
                get_text("download_hf_token"),
                type="password",
                key="hf_token_input",
                placeholder=get_text("download_hf_token_placeholder")
            )
        
        with col2:
            st.markdown("""
            <div style="padding-top: 8px;">
            <a href="https://huggingface.co/settings/tokens" target="_blank">
                <button style="width: 100%; padding: 8px;">取得 Token</button>
            </a>
            </div>
            """, unsafe_allow_html=True)
        
        st.caption(get_text("download_token_help"))
    else:
        hf_token_input = None
    
    # 下載按鈕 - 當下載中時 disabled
    if selected_model:
        col_btn1, col_btn2 = st.columns([1, 1])
        
        # 檢查目錄是否已存在
        target_path = MODELS_DIR / selected_model["local_dir"]
        dir_exists = target_path.exists() and len(list(target_path.iterdir())) > 0
        
        with col_btn1:
            download_disabled = st.session_state.is_downloading
            # 根據目錄是否存在改變按鈕文字
            btn_label = get_text("download_btn_overwrite") if dir_exists else get_text("download_btn")
            
            if st.button(
                btn_label, 
                type="primary", 
                key="download_btn",
                disabled=download_disabled
            ):
                st.session_state.is_downloading = True
                st.rerun()
        
        # 取消按鈕 - 只在下載中時顯示
        with col_btn2:
            if st.session_state.is_downloading:
                if st.button(get_text("download_cancel"), key="cancel_btn", type="secondary"):
                    st.session_state.is_downloading = False
                    st.session_state.download_status = "cancelled"
                    # 添加取消訊息到輸出（清晰顯示取消）
                    st.session_state.download_output = f"[{get_text('cancel')}] {get_text('download_cancelled')}\n"
                    st.warning(f"⚠️ {get_text('download_cancelled')}")
                    st.rerun()
        
        # 顯示警告（如果目錄存在）
        if dir_exists:
            st.warning(f"⚠️ {get_text('download_dir_exists')}")
        
        # 執行下載
        if st.session_state.is_downloading:
            # 清空之前的下載輸出
            st.session_state.download_output = ""
            st.session_state.download_status = None
            
            # 準備要使用的 Token
            token_to_use = None
            
            # 優先使用新輸入的 Token
            if hf_token_input:
                token_to_use = hf_token_input
                # 保存新 Token
                save_hf_token(hf_token_input)
                st.session_state.hf_token = hf_token_input
            # 其次使用保存的 Token
            elif saved_token:
                token_to_use = saved_token
            
            # 顯示進度條和狀態
            progress_bar = st.progress(0, text=get_text("preparing_download"))
            status_text = st.empty()
            output_container = st.empty()
            
            def update_progress(text):
                """更新進度顯示"""
                output_container.markdown(
                    f'<div class="console-output">{text.replace("<", "&lt;").replace(">", "&gt;")}</div>',
                    unsafe_allow_html=True
                )
                # 根據進度文字更新進度條
                if "開始下載檔案" in text or "开始下载文件" in text or "Starting download" in text:
                    progress_bar.progress(20, text=get_text("starting_download"))
                elif "下載完成" in text or "下载完成" in text or "Download Complete" in text:
                    progress_bar.progress(100, text=get_text("download_complete"))
                elif "正在連接" in text or "正在连接" in text or "Connecting" in text:
                    progress_bar.progress(10, text=get_text("connecting"))
                else:
                    progress_bar.progress(50, text=get_text("downloading"))
            
            try:
                status_text.info(" " + get_text("preparing_download_status"))
                returncode, output = download_model(
                    selected_model["model_id"],
                    selected_model["local_dir"],
                    token_to_use,
                    progress_callback=update_progress,
                    process_state=st.session_state
                )
                
                st.session_state.download_output = output
                
                if returncode == 0:
                    st.session_state.download_status = "success"
                    progress_bar.progress(100, text=get_text("progress_download_complete"))
                    status_text.success(get_text("download_success"))
                elif returncode == -1:
                    st.session_state.download_status = "auth_required"
                    progress_bar.progress(0, text=get_text("progress_auth_failed"))
                    status_text.warning(get_text("download_hf_login"))
                else:
                    st.session_state.download_status = "failed"
                    progress_bar.progress(0, text=get_text("progress_download_failed"))
                    status_text.error(get_text("download_failed"))
            except Exception as e:
                st.session_state.download_status = "failed"
                progress_bar.progress(0, text=get_text("progress_error_occurred"))
                status_text.error(f"{get_text('download_failed')}: {str(e)}")
            finally:
                # 下載完成或出錯，重置下載狀態
                st.session_state.is_downloading = False
                st.rerun()
    
    # 顯示下載輸出
    if st.session_state.download_output:
        st.subheader(get_text("download_console"))
        st.markdown(
            f'<div class="console-output" id="download-console">{st.session_state.download_output.replace("<", "&lt;").replace(">", "&gt;")}</div>',
            unsafe_allow_html=True
        )
        st.markdown("""
            <script>
            function scrollConsoleToBottom(elementId) {
                const element = document.getElementById(elementId);
                if (element) {
                    // 立即滾動
                    element.scrollTop = element.scrollHeight;
                    
                    // 監聽內容變化並持續滾動
                    const observer = new MutationObserver(() => {
                        element.scrollTop = element.scrollHeight;
                    });
                    
                    observer.observe(element, {
                        childList: true,
                        subtree: true,
                        characterData: true
                    });
                }
            }
            
            // 初始滾動 + 監聽
            scrollConsoleToBottom('download-console');
            
            // 定期檢查（每200ms），確保持續滾動
            setInterval(() => {
                const element = document.getElementById('download-console');
                if (element) {
                    element.scrollTop = element.scrollHeight;
                }
            }, 200);
            </script>
        """, unsafe_allow_html=True)

# ==============================
# Tab 5: 資料轉換
# ==============================
with tab_convert:
    st.header(get_text("convert_title"))
    
    # 轉換方向選擇
    convert_mode = st.radio(
        get_text("convert_select_direction"),
        [get_text("convert_excel_to_json"), get_text("convert_json_to_excel")],
        horizontal=True
    )
    
    st.divider()
    
    if convert_mode == get_text("convert_excel_to_json"):
        # Excel → JSON 轉換
        st.subheader(get_text("convert_excel_to_json"))
        
        uploaded_excel = st.file_uploader(
            get_text("convert_select_excel"),
            type=["xlsx"],
            key="convert_excel_uploader"
        )
        
        if uploaded_excel is not None:
            # 保存上傳的檔案到臨時位置
            temp_excel_path = f"/tmp/{uploaded_excel.name}"
            os.makedirs("/tmp", exist_ok=True)
            with open(temp_excel_path, "wb") as f:
                f.write(uploaded_excel.getbuffer())
            
            if st.button(get_text("convert_btn"), key="convert_excel_btn", type="primary"):
                try:
                    with st.spinner(get_text("convert_converting")):
                        # 動態導入轉換腳本
                        import sys
                        sys.path.insert(0, str(SCRIPTS_DIR))
                        from excel_to_json import convert_excel_to_json
                        
                        convert_excel_to_json(temp_excel_path)
                        
                        # 找到輸出檔
                        output_json = temp_excel_path.replace(".xlsx", ".json")
                        
                        if os.path.exists(output_json):
                            with open(output_json, "r", encoding="utf-8") as f:
                                json_content = f.read()
                            
                            st.success(get_text("convert_success"))
                            st.download_button(
                                label=get_text("convert_download"),
                                data=json_content,
                                file_name=f"{uploaded_excel.name.replace('.xlsx', '.json')}",
                                mime="application/json"
                            )
                except Exception as e:
                    st.error(f"{get_text('convert_failed')}: {str(e)}")
    
    else:
        # JSON → Excel 轉換
        st.subheader(get_text("convert_json_to_excel"))
        
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_json = st.file_uploader(
                get_text("convert_select_json"),
                type=["json"],
                key="convert_json_uploader"
            )
        
        with col2:
            uploaded_template = st.file_uploader(
                get_text("convert_template"),
                type=["xlsx"],
                key="convert_template_uploader"
            )
        
        if uploaded_json is not None and uploaded_template is not None:
            # 保存上傳的檔案到臨時位置
            temp_json_path = f"/tmp/{uploaded_json.name}"
            temp_excel_path = f"/tmp/{uploaded_template.name}"
            os.makedirs("/tmp", exist_ok=True)
            
            with open(temp_json_path, "wb") as f:
                f.write(uploaded_json.getbuffer())
            with open(temp_excel_path, "wb") as f:
                f.write(uploaded_template.getbuffer())
            
            if st.button(get_text("convert_btn"), key="convert_json_btn", type="primary"):
                try:
                    with st.spinner(get_text("convert_converting")):
                        # 動態導入轉換腳本
                        import sys
                        sys.path.insert(0, str(SCRIPTS_DIR))
                        from write_json_to_excel import write_json_to_excel
                        
                        write_json_to_excel(temp_excel_path, temp_json_path)
                        
                        # 找到輸出檔
                        output_excel = temp_excel_path.replace(".xlsx", "_output.xlsx")
                        
                        if os.path.exists(output_excel):
                            with open(output_excel, "rb") as f:
                                excel_content = f.read()
                            
                            st.success(get_text("convert_success"))
                            st.download_button(
                                label=get_text("convert_download"),
                                data=excel_content,
                                file_name=f"{uploaded_template.name.replace('.xlsx', '_output.xlsx')}",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                except Exception as e:
                    st.error(f"{get_text('convert_failed')}: {str(e)}")

# ==============================
# 底部信息
# ==============================
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 12px;">
    <p> AI Behavior Research Platform | Powered by Streamlit</p>
    <p>Project Root: {}</p>
</div>
""".format(PROJECT_ROOT), unsafe_allow_html=True)
