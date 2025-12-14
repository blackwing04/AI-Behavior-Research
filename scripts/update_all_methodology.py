#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from pathlib import Path

# 動態獲取專案根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 讀取繁體版本已更新的新內容
tw_file = PROJECT_ROOT / 'doc' / 'theory' / 'zh-TW' / 'THEORETICAL_FOUNDATION_TW.md'
with open(tw_file, 'r', encoding='utf-8') as f:
    tw_content = f.read()

# 提取繁體版的新方法論設計部分（從新的 Mermaid 圖表開始）
start_idx = tw_content.find('#### 方法論流程圖')
if start_idx == -1:
    print(" 找不到 zh-TW 中的新方法論流程圖")
    exit(1)

end_idx = tw_content.find('### 第一層：意義方程式作為驗證標準', start_idx)
if end_idx == -1:
    print(" 找不到結束位置")
    exit(1)

# 提取新內容（包含標題和整個方法論圖表部分）
new_flowchart_section = tw_content[start_idx:end_idx].rstrip()

print(" 從繁體版提取了新方法論流程圖部分")

# 為簡體版本調整中文
simplified_content = new_flowchart_section.replace('方法論流程圖', '方法论流程图')
simplified_content = simplified_content.replace('推理層', '推理层')
simplified_content = simplified_content.replace('框架層', '框架层')
simplified_content = simplified_content.replace('固化層', '固化层')
simplified_content = simplified_content.replace('長期互動', '长期互动')
simplified_content = simplified_content.replace('觀察行為模式', '观察行为模式')
simplified_content = simplified_content.replace('本能方程式', '本能方程式')
simplified_content = simplified_content.replace('分解行為驅動力', '分解行为驱动力')
simplified_content = simplified_content.replace('意義方程式', '意义方程式')
simplified_content = simplified_content.replace('驗證框架品質', '验证框架品质')
simplified_content = simplified_content.replace('設計穩定的行為框架', '设计稳定的行为框架')
simplified_content = simplified_content.replace('QLoRA 訓練', 'QLoRA 训练')
simplified_content = simplified_content.replace('內化為模型參數', '内化为模型参数')
simplified_content = simplified_content.replace('驗證', '验证')
simplified_content = simplified_content.replace('是否達標', '是否达标')
simplified_content = simplified_content.replace('穩定的AI個體', '稳定的AI个体')
simplified_content = simplified_content.replace('層級', '层级')
simplified_content = simplified_content.replace('識別行為的驅動因素', '识别行为的驱动因素')
simplified_content = simplified_content.replace('分析情境影響', '分析情景影响')
simplified_content = simplified_content.replace('啟動反思層的修正', '启动反思层的修正')
simplified_content = simplified_content.replace('評估內部一致性', '评估内部一致性')
simplified_content = simplified_content.replace('評估外部共鳴度', '评估外部共鸣度')
simplified_content = simplified_content.replace('將推理形成的框架固化', '将推理形成的框架固化')
simplified_content = simplified_content.replace('參數', '参数')
simplified_content = simplified_content.replace('實現穩定的行為遷移', '实现稳定的行为迁移')
simplified_content = simplified_content.replace('三層結構詳解', '三层结构详解')

# 為英文版本調整
english_content = simplified_content.replace('方法论流程图', 'Methodology Flowchart')
english_content = english_content.replace('推理层', 'Reasoning Layer')
english_content = english_content.replace('框架层', 'Framework Layer')
english_content = english_content.replace('固化层', 'Solidification Layer')
english_content = english_content.replace('长期互动', 'Long-term Interaction')
# ... 需要手動調整英文版本

print(f"\n 簡體版本準備就緒")
print(f"內容大小: {len(simplified_content)} 字符")

# 更新簡體版本
print("\n正在更新 zh-CN 版本...")
cn_file = PROJECT_ROOT / 'doc' / 'theory' / 'zh-CN' / 'THEORETICAL_FOUNDATION_CN.md'
try:
    with open(cn_file, 'r', encoding='utf-8') as f:
        cn_content = f.read()
    
    # 查找舊的方法論架構部分並替換
    old_start = '#### 三层结构详解'
    new_position = cn_content.find(old_start)
    
    if new_position != -1:
        # 找到舊的圖表部分開始位置
        old_chart_start = cn_content.rfind('【方法论架构】', 0, new_position)
        if old_chart_start != -1:
            # 找到三層結構詳解的開始
            old_end = cn_content.find('### 第一層', new_position)
            if old_end != -1:
                # 替換
                cn_content = cn_content[:old_chart_start] + simplified_content + '\n\n' + cn_content[old_end:]
                
                with open(cn_file, 'w', encoding='utf-8') as f:
                    f.write(cn_content)
                
                print(" zh-CN 已更新")
            else:
                print(" 找不到結束位置")
        else:
            print(" 找不到舊圖表位置")
    else:
        print(" 找不到三層結構詳解標題")
        
except Exception as e:
    print(f" 錯誤: {e}")

print("\n處理完成！")
