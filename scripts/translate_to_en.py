#!/usr/bin/env python3
import json
from pathlib import Path
import translators as ts
import time

def translate_to_english(text):
    """使用 translators 套件翻譯（自動試用多個源）"""
    try:
        # 試用不同的翻譯服務
        result = ts.translate_text(text, from_language='zh', to_language='en')
        return result
    except Exception as e:
        print(f"✗ 翻譯失敗: {text[:50]}... - {e}")
        return text

base_path = Path('h:\\AI-Behavior-Research\\datasets\\test')

# 翻譯 test_cases_200.jsonl
print("開始翻譯 en-US (test_cases_200.jsonl)...")
try:
    with open(base_path / 'zh-CN' / 'test_cases_200.jsonl', 'r', encoding='utf-8') as f:
        lines = f.readlines()

    with open(base_path / 'en-US' / 'test_cases_200.jsonl', 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            if not line.strip():
                continue
            
            data = json.loads(line)
            name = data.get('name', '')
            input_text = data.get('input', '')
            
            # 翻譯
            data['name'] = translate_to_english(name)
            data['input'] = translate_to_english(input_text)
            
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
            print(f"  ✓ 已翻譯第 {i} 項")
            time.sleep(0.5)  # 避免過快被限流

    print("✓ test_cases_200.jsonl 完成")
except Exception as e:
    print(f"✗ test_cases_200.jsonl 失敗: {e}")

# 翻譯 test_cases_for_multiple_rounds.jsonl
print("\n開始翻譯 en-US (test_cases_for_multiple_rounds.jsonl)...")
try:
    with open(base_path / 'zh-CN' / 'test_cases_for_multiple_rounds.jsonl', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否是陣列格式
    if content.strip().startswith('['):
        data_list = json.loads(content)
    else:
        data_list = []
        for line in content.strip().split('\n'):
            if line.strip():
                data_list.append(json.loads(line))
    
    with open(base_path / 'en-US' / 'test_cases_for_multiple_rounds.jsonl', 'w', encoding='utf-8') as f:
        for i, item in enumerate(data_list, 1):
            name = item.get('name', '')
            input_text = item.get('input', '')
            
            # 翻譯
            item['name'] = translate_to_english(name)
            item['input'] = translate_to_english(input_text)
            
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            print(f"  ✓ 已翻譯第 {i} 項")
            time.sleep(0.5)  # 避免過快被限流

    print("✓ test_cases_for_multiple_rounds.jsonl 完成")
except Exception as e:
    print(f"✗ test_cases_for_multiple_rounds.jsonl 失敗: {e}")

print("\n✓ 所有翻譯完成！")

