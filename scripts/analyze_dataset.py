#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import re
import sys

dataset_path = r'h:\AI-Behavior-Research\datasets\behavior\V4\behavior_dataset.jsonl'

with open(dataset_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    # 統計所有 ID 類型
    id_types = {}
    tags_freq = {}
    
    for i, line in enumerate(lines):
        try:
            data = json.loads(line)
            full_id = data['id']
            
            # 提取 ID 的主要部分（從開始到最後一個數字段）
            # 例如: 'pronoun_disambiguation_001' → 'pronoun_disambiguation'
            #       'e_module_401' → 'e_module'
            #       'law_001' → 'law'
            import re
            match = re.match(r'^(.+?)_\d+$', full_id)
            if match:
                id_type = match.group(1)
            else:
                id_type = full_id
            
            id_types[id_type] = id_types.get(id_type, 0) + 1
            
            # 統計標籤
            for tag in data.get('tags', []):
                tags_freq[tag] = tags_freq.get(tag, 0) + 1
        except json.JSONDecodeError as e:
            print(f"行 {i+1} JSON 錯誤: {str(e)[:50]}")
            continue
    
    print('=== V4.5 訓練集統計 ===\n')
    print('ID 類型分佈 (前15):')
    for k, v in sorted(id_types.items(), key=lambda x: -x[1])[:15]:
        print(f'  {k}: {v}')
    
    print(f'\n總 ID 類型數: {len(id_types)}')
    print(f'總訓練項: {sum(id_types.values())}')
    
    print('\n最常見的標籤 (前15):')
    for k, v in sorted(tags_freq.items(), key=lambda x: -x[1])[:15]:
        print(f'  {k}: {v}')
