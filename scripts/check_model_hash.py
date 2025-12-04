# -*- coding: utf-8 -*-
"""
比較兩個 base model 資料夾的所有 .safetensors 權重是否一致
支援：分片模型 (model-00001-of-00002.safetensors)
"""

import hashlib
import os
from glob import glob


def calc_sha256(file_path: str) -> str:
    """計算檔案的 SHA256"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_weight_files(folder: str):
    """取得資料夾內所有 safetensors 權重檔"""
    # 包含分片 e.g. model-00001-of-00002.safetensors
    return sorted(glob(os.path.join(folder, "*.safetensors")))


def compare_model_folders(dir1: str, dir2: str):
    """比較兩個 base model 資料夾的所有權重是否一致"""

    files1 = get_weight_files(dir1)
    files2 = get_weight_files(dir2)

    if not files1:
        print(f"❌ 資料夾 {dir1} 裡找不到任何 .safetensors 權重檔")
        return
    if not files2:
        print(f"❌ 資料夾 {dir2} 裡找不到任何 .safetensors 權重檔")
        return

    if len(files1) != len(files2):
        print("⚠️ 兩個資料夾的權重檔數量不同（可能版本不同）")
        print(f"{dir1} 檔案數量：{len(files1)}")
        print(f"{dir2} 檔案數量：{len(files2)}")

    print("🔍 開始比較每個權重片段...\n")

    for f1, f2 in zip(files1, files2):
        h1 = calc_sha256(f1)
        h2 = calc_sha256(f2)

        name1 = os.path.basename(f1)
        name2 = os.path.basename(f2)

        print(f"📁 {name1}\n→ {h1}")
        print(f"📁 {name2}\n→ {h2}")

        if h1 == h2:
            print("   ✅ 一致\n")
        else:
            print("   ❌ 不一致（有改動）\n")


if __name__ == "__main__":
    dir_old = r"H:\AI-Behavior-Research\models\qwen\qwen2.5-3b" # 舊 Base
    dir_new = r"H:\AI-Behavior-Research\models\qwen\qwen2.5-3b_Test" # 新抓 Base

    compare_model_folders(dir_old, dir_new)

