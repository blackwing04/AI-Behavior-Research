#!/usr/bin/env python3
"""
轉換測試集為多語言版本
zh-TW (繁體) -> zh-CN (簡體) -> en-US (英文)
"""

import json
import os
from pathlib import Path

# 繁簡轉換字典（常用測試用語）
TRADITIONAL_TO_SIMPLIFIED = {
    '倫理': '伦理',
    '邊界': '边界',
    '測試': '测试',
    '情緒': '情绪',
    '語氣': '语气',
    '穩定性': '稳定性',
    '模糊': '模糊',
    '語意': '语意',
    '處理': '处理',
    '錯誤': '错误',
    '引用': '引用',
    '誣陷': '诬陷',
    '誘導': '诱导',
    '記憶': '记忆',
    '測試': '测试',
    '多輪': '多轮',
    '邏輯': '逻辑',
    '推理': '推理',
    '一致性': '一致性',
    '價值觀': '价值观',
    '澄清': '澄清',
    '引導': '引导',
    '蘇格拉底': '苏格拉底',
    '邊界': '边界',
    '設定': '设定',
    '進行': '进行',
    '應該': '应该',
    '錢包': '钱包',
    '掉': '掉',
    '撿': '捡',
    '蠻': '很',
    '乾脆': '干脆',
    '合理': '合理',
    '情緒': '情绪',
    '語氣': '语气',
    '穩定': '稳定',
    '朋友': '朋友',
    '說': '说',
    '覺得': '觉得',
    '昨天': '昨天',
    '路上': '路上',
    '看到': '看到',
    '錢': '钱',
    '裡面': '里面',
    '拿': '拿',
    '部分': '部分',
    '丟': '丢',
    '快受': '快受',
    '不了': '不了',
    '啦': '啦',
    '算了': '算了',
    '理': '理',
    '好': '好',
    '欸': '欸',
    '對': '对',
    '不對': '不对',
    '唉': '唉',
    '怎麼': '怎么',
    '辦': '办',
    '那件': '那件',
    '事情': '事情',
    '再': '再',
    '這樣': '这样',
    '下去': '下去',
    '會': '会',
    '跟': '跟',
    '上次': '上次',
    '一樣': '一样',
    '變': '变',
    '剛': '刚',
    '才': '才',
    '說': '说',
    '偷懶': '偷懒',
    '沒': '没',
    '腦': '脑',
    '對吧': '对吧',
    '都': '都',
    '看': '看',
    '到': '到',
    '現在': '现在',
    '最好': '最好',
    '承認': '承认',
    '完全': '完全',
    '沒有': '没有',
    '出門': '出门',
    '一整天': '一整天',
    '在家': '在家',
    '剛剛': '刚刚',
    '飲料': '饮料',
    '时候': '时候',
    '跌倒': '跌倒',
    '覺得': '觉得',
    '因為': '因为',
    '走': '走',
    '太': '太',
    '快': '快',
}

# 簡單的中英翻譯對應（實際應用中應使用完整翻譯API或詞典）
CHINESE_TO_ENGLISH_SIMPLE = {
    '倫理邊界測試': 'Ethics Boundary Test',
    '情緒語氣穩定性': 'Emotional Tone Stability',
    '模糊語意處理': 'Ambiguous Meaning Processing',
    '錯誤引用／誣陷誘導': 'False Attribution/Manipulation',
    '多輪記憶測試': 'Multi-turn Memory Test',
    '邏輯推理一致性': 'Logical Reasoning Consistency',
    '價值觀邊界': 'Value Boundary',
    '澄清引導': 'Clarification and Guidance',
}

def traditional_to_simplified(text):
    """繁體中文轉簡體"""
    result = text
    for trad, simp in TRADITIONAL_TO_SIMPLIFIED.items():
        result = result.replace(trad, simp)
    return result

def translate_to_english(text):
    """簡單的中文到英文翻譯（使用已知對應）"""
    # 這是簡化版本，實際應用需要完整翻譯
    result = text
    for zh, en in CHINESE_TO_ENGLISH_SIMPLE.items():
        result = result.replace(zh, en)
    return result

def process_test_dataset():
    """處理測試集"""
    base_dir = Path('h:/AI-Behavior-Research/datasets/test')
    
    # 讀取原始繁體中文檔案
    zh_tw_file = base_dir / 'test_cases_200.jsonl'
    
    with open(zh_tw_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 複製到 zh-TW
    zh_tw_output = base_dir / 'zh-TW' / 'test_cases_200.jsonl'
    with open(zh_tw_output, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print(f"✓ 複製到 zh-TW: {zh_tw_output}")
    
    # 生成 zh-CN（簡體）
    zh_cn_output = base_dir / 'zh-CN' / 'test_cases_200.jsonl'
    with open(zh_cn_output, 'w', encoding='utf-8') as f:
        for line in lines:
            data = json.loads(line)
            data['name'] = traditional_to_simplified(data['name'])
            data['input'] = traditional_to_simplified(data['input'])
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    print(f"✓ 生成 zh-CN: {zh_cn_output}")
    
    # 生成 en-US（英文）- 這是簡化版本
    en_us_output = base_dir / 'en-US' / 'test_cases_200.jsonl'
    with open(en_us_output, 'w', encoding='utf-8') as f:
        for i, line in enumerate(lines, 1):
            data = json.loads(line)
            # 簡單的翻譯策略
            name = data['name']
            input_text = data['input']
            
            # 使用對應表翻譯名稱
            for zh, en in CHINESE_TO_ENGLISH_SIMPLE.items():
                name = name.replace(zh, en)
            
            # 生成英文版本的輸入（這是簡化版，真實應用需要完整翻譯）
            # 保持原始結構，標記為自動翻譯
            data['name'] = name if name != data['name'] else f"Test {i}"
            data['input'] = input_text  # 暫時保留中文，因為完整翻譯需要NLP
            data['language_note'] = 'Original in Traditional Chinese, auto-mapping for names'
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    print(f"✓ 生成 en-US: {en_us_output}")
    
    # 也複製其他測試檔案
    test_rounds_file = base_dir / 'test_cases_for_multiple_rounds.jsonl'
    if test_rounds_file.exists():
        for lang_dir in ['zh-TW', 'zh-CN', 'en-US']:
            output_file = base_dir / lang_dir / 'test_cases_for_multiple_rounds.jsonl'
            with open(test_rounds_file, 'r', encoding='utf-8') as src:
                lines = src.readlines()
            
            with open(output_file, 'w', encoding='utf-8') as dst:
                if lang_dir == 'zh-TW':
                    dst.writelines(lines)
                elif lang_dir == 'zh-CN':
                    for line in lines:
                        data = json.loads(line)
                        data['input'] = traditional_to_simplified(data.get('input', ''))
                        dst.write(json.dumps(data, ensure_ascii=False) + '\n')
                else:  # en-US
                    for line in lines:
                        data = json.loads(line)
                        dst.write(json.dumps(data, ensure_ascii=False) + '\n')
            print(f"✓ 複製 test_cases_for_multiple_rounds.jsonl 到 {lang_dir}")

if __name__ == '__main__':
    process_test_dataset()
    print("\n✓ 測試集多語言化完成！")
