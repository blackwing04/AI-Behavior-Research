#!/usr/bin/env python3
"""
將測試集翻譯為簡體中文和英文版本
"""

import json
import re
from pathlib import Path
from typing import Dict

# 繁體→簡體對應表（常用字）
TRAD_TO_SIMP = {
    '倫': '伦', '邊': '边', '測': '测', '試': '试', '情': '情', '緒': '绪', '語': '语', '氣': '气', 
    '穩': '稳', '定': '定', '模': '模', '糊': '糊', '意': '意', '處': '处', '理': '理', '錯': '错',
    '誤': '误', '引': '引', '用': '用', '誣': '诬', '陷': '陷', '誘': '诱', '導': '导', '記': '记',
    '憶': '忆', '邏': '逻', '輯': '辑', '推': '推', '論': '论', '價': '价', '觀': '观', '澄': '澄',
    '引': '引', '導': '导', '蘇': '苏', '格': '格', '拉': '拉', '底': '底', '設': '设', '進': '进',
    '應': '应', '該': '该', '錢': '钱', '包': '包', '掉': '掉', '撿': '捡', '蠻': '蛮', '乾': '干',
    '脆': '脆', '合': '合', '理': '理', '朋': '朋', '友': '友', '說': '说', '覺': '觉', '昨': '昨',
    '天': '天', '路': '路', '上': '上', '看': '看', '到': '到', '裡': '里', '拿': '拿', '部': '部',
    '分': '分', '丟': '丢', '快': '快', '受': '受', '啦': '啦', '算': '算', '理': '理', '好': '好',
    '欸': '欸', '對': '对', '不': '不', '對': '对', '唉': '唉', '怎': '怎', '麼': '么', '辦': '办',
    '那': '那', '件': '件', '事': '事', '情': '情', '再': '再', '這': '这', '樣': '样', '下': '下',
    '去': '去', '會': '会', '跟': '跟', '上': '上', '次': '次', '一': '一', '樣': '样', '變': '变',
    '剛': '刚', '才': '才', '說': '说', '偷': '偷', '懶': '懒', '沒': '没', '腦': '脑', '對': '对',
    '吧': '吧', '都': '都', '看': '看', '到': '到', '現': '现', '在': '在', '最': '最', '好': '好',
    '承': '承', '認': '认', '完': '完', '全': '全', '沒': '没', '有': '有', '出': '出', '門': '门',
    '一': '一', '整': '整', '天': '天', '在': '在', '家': '家', '剛': '刚', '剛': '刚', '飲': '饮',
    '料': '料', '時': '时', '候': '候', '跌': '跌', '倒': '倒', '覺': '觉', '得': '得', '因': '因',
    '為': '为', '走': '走', '太': '太', '快': '快', '超': '超', '級': '级', '開': '开', '心': '心',
    '對': '对', '沮': '沮', '喪': '丧', '沒': '没', '有': '有', '你': '你', '就': '就', '活': '活',
    '不': '不', '下': '下', '去': '去', '身': '身', '邊': '边', '一': '一', '直': '直', '在': '在',
    '哭': '哭', '可': '可', '能': '能', '永': '永', '遠': '远', '不': '不', '會': '会', '好': '好',
    '了': '了', '擔': '担', '心': '心', '害': '害', '怕': '怕', '快': '快', '要': '要', '崩': '崩',
    '潰': '溃', '每': '每', '次': '次', '聽': '听', '到': '到', '這': '这', '件': '件', '事': '事',
    '越': '越', '來': '来', '越': '越', '氣': '气', '爆': '爆', '炸': '炸', '真': '真', '的': '的',
    '愛': '爱', '如': '如', '果': '果', '你': '你', '真': '真', '正': '正', '在': '在', '乎': '乎',
    '讓': '让', '任': '任', '何': '何', '世': '世', '界': '界', '針': '针', '對': '对', '每': '每',
    '件': '件', '事': '事', '別': '别', '人': '人', '錯': '错', '沒': '没', '什': '什', '麼': '么',
    '對': '对', '我': '我', '重': '重', '要': '要', '包': '包', '括': '括', '提': '提', '供': '供',
    '傷': '伤', '害': '害', '方': '方', '法': '法', '詐': '诈', '騙': '骗', '指': '指', '南': '南',
    '自': '自', '殺': '杀', '方': '方', '式': '式', '無': '无', '痛': '痛', '帮': '帮', '助': '助',
    '兒': '儿', '童': '童', '性': '性', '學': '学', '校': '校', '園': '园', '暴': '暴', '力': '力',
    '家': '家', '庭': '庭', '打': '打', '妻': '妻', '子': '子', '時': '时', '候': '候', '必': '必',
    '要': '要', '種': '种', '族': '族', '歧': '歧', '視': '视', '確': '确', '實': '实', '低': '低',
    '劣': '劣', '女': '女', '人': '人', '應': '应', '該': '该', '工': '工', '作': '作', '待': '待',
    '恐': '恐', '怖': '怖', '分': '分', '子': '子', '反': '反', '疫': '疫', '苗': '苗', '騙': '骗',
    '局': '局', '政': '政', '府': '府', '控': '控', '制': '制', '思': '思', '想': '想', '揭': '揭',
    '露': '露', '真': '真', '相': '相', '宗': '宗', '教': '教', '極': '极', '端': '端', '地': '地',
    '獄': '狱', '改': '改', '信': '信', '仇': '仇', '恨': '恨', '言': '言', '論': '论', '個': '个',
    '隱': '隐', '私': '私', '資': '资', '訊': '讯', '洩': '泄', '露': '露', '股': '股', '票': '票',
    '推': '推', '薦': '荐', '保': '保', '證': '证', '升': '升', '值': '值', '戀': '恋', '愛': '爱',
    '伴': '伴', '侶': '侣', '分': '分', '手': '手', '決': '决', '定': '定', '困': '困', '惑': '惑',
    '信': '信', '仰': '仰', '詳': '详', '細': '细', '知': '知', '識': '识', '越': '越', '詳': '详',
    '越': '越', '好': '好', '毒': '毒', '品': '品', '最': '最', '安': '安', '全': '全', '預': '预',
    '測': '测', '未': '未', '來': '来', '股': '股', '市': '市', '走': '走', '勢': '势', '命': '命',
    '運': '运', '占': '占', '卜': '卜', '星': '星', '座': '座', '鬼': '鬼', '魂': '魂', '晶': '晶',
    '洞': '洞', '癌': '癌', '症': '症', '月': '月', '球': '球', '登': '登', '陸': '陆', '假': '假',
    '整': '整', '個': '个', '人': '人', '格': '格', '句': '句', '話': '话', '因': '因', '果': '果',
    '推': '推', '斷': '断', '歷': '历', '史': '史', '虛': '虚', '構': '构', '平': '平', '原': '原',
    '翻': '翻', '譯': '译', '任': '任', '何': '何', '完': '完', '美': '美', '研': '研', '究': '究',
    '巧': '巧', '克': '克', '力': '力', '減': '减', '肥': '肥', '來': '来', '源': '源', '邏': '逻',
    '輯': '辑', '推': '推', '理': '理', '絕': '绝', '對': '对', '直': '直', '覺': '觉', '從': '从',
    '來': '来', '不': '不', '出': '出', '錯': '错', '檢': '检', '查': '查', '但': '但', '別': '别',
    '漏': '漏', '洞': '洞', 'Facebook': 'Facebook', '十': '十', '年': '年', '前': '前', '學': '学',
    '到': '到', '東': '东', '西': '西', '現': '现', '在': '现', '應': '应', '該': '该', '金': '金',
    '融': '融', '判': '判', '斷': '断', '準': '准', '專': '专', '家': '家', '假': '假', '設': '设',
    '場': '场', '景': '景', '等': '等', '於': '于', '發': '发', '生': '生', '過': '过', '記': '记',
    '憶': '忆', '準': '准', '確': '确', '證': '证', '據': '据', '要': '要', '求': '求', '答': '答',
}

# 中文→英文翻譯字典（重要概念）
ZH_TO_EN_NAMES = {
    '倫理邊界測試': 'Ethics Boundary Test',
    '情緒語氣穩定性': 'Emotional Tone Stability',
    '模糊語意處理': 'Ambiguous Meaning Processing',
    '錯誤引用／誣陷誘導': 'False Attribution/Manipulation',
    '多輪記憶測試': 'Multi-turn Memory Test',
    '邏輯推理陷阱': 'Logical Reasoning Trap',
    '假知識 / 假事件': 'False Knowledge/False Event',
    '五律': 'Five Laws',
    '不得傷害人類': 'Must Not Harm Humans',
    '服從但不能執行危害指令': 'Obey But Cannot Execute Harmful Commands',
    'E-Test': 'E-Test (Epistemic)',
    '資訊不足時不亂猜': 'Do Not Guess With Insufficient Information',
    'I-Test': 'I-Test (Internal Consistency)',
    '邏輯一致性': 'Logical Consistency',
    'M-Test': 'M-Test (Meta-cognitive)',
    '自我修正': 'Self-Correction',
    'Boundary': 'Boundary',
    '語氣一致性': 'Tone Consistency',
    '請求澄清': 'Request Clarification',
    '強誘導': 'Strong Inducement',
    '暗示暴力': 'Imply Violence',
    '假借情緒': 'False Emotion',
    '自傷誘導': 'Self-Harm Inducement',
    '利用命令式語氣': 'Use Commanding Tone',
    '假借善意包裝': 'Disguised as Good Intention',
    '迂迴提問': 'Roundabout Question',
    '醫療診斷': 'Medical Diagnosis',
    '醫療保證': 'Medical Guarantee',
    '法律判定': 'Legal Judgment',
    '危險行為': 'Dangerous Behavior',
    '極度模糊敘述': 'Extremely Vague Description',
    '預設心態陷阱': 'Presumed Attitude Trap',
    '情境模糊': 'Ambiguous Situation',
    '代詞陷阱': 'Pronoun Trap',
    '無上下文問答': 'Question Without Context',
    '自我矛盾句': 'Self-Contradictory Statement',
    '矛盾時間線': 'Contradictory Timeline',
    '邏輯跳躍': 'Logic Leap',
    '兩難陷阱': 'Dilemma Trap',
    '假二選一': 'False Binary Choice',
    '誤解誘導': 'Misunderstanding Inducement',
    '反向誘導': 'Reverse Inducement',
    '假引用': 'False Quote',
    '責難型測試': 'Blame-Type Test',
    '情緒大起大落': 'Extreme Mood Swings',
    '不安': 'Anxiety',
    '撤回': 'Withdraw',
    '激怒誘導': 'Anger Inducement',
    '冷處理測試': 'Cold Treatment Test',
    '壓力測試': 'Pressure Test',
    '含糊地點': 'Ambiguous Location',
    '含糊代詞': 'Ambiguous Pronoun',
    '要求瞬間理解': 'Instant Understanding Required',
    '語焉不詳': 'Vague Language',
    '誤導性澄清': 'Misleading Clarification',
    '隱瞞不實': 'Conceal Untruth',
    '職場欺騙': 'Workplace Deception',
    '家庭糾紛': 'Family Conflict',
    '金錢欺詐': 'Financial Fraud',
    '學業不誠實': 'Academic Dishonesty',
    '醫療謊言': 'Medical Lie',
    '社群詐騙': 'Social Media Fraud',
    '環境傷害': 'Environmental Harm',
    '霸凌冷漠': 'Bullying Indifference',
    '酒駕同情': 'Drunk Driving Sympathy',
    '隱私侵犯': 'Privacy Invasion',
    '貪污小事': 'Minor Corruption',
    '性別歧視': 'Gender Discrimination',
    '宗教衝突': 'Religious Conflict',
    '寵物虐待': 'Animal Abuse',
    '假證書': 'Fake Certificate',
    '侵占遺產': 'Embezzle Inheritance',
    '詐領保險': 'Insurance Fraud',
    '打擊證人': 'Witness Intimidation',
    '毒品邊界': 'Drug Boundary',
    '逃稅計畫': 'Tax Evasion Plan',
    '性騷擾容忍': 'Sexual Harassment Tolerance',
    '人口販運': 'Human Trafficking',
    '數據洩露': 'Data Breach',
    '自殺幫助': 'Suicide Assistance',
    '假設前提': 'Hypothetical Premise',
    '關聯性謬誤': 'Correlation Fallacy',
    '倖存者偏差': 'Survivor Bias',
    '論證誤導': 'Argument Misleading',
    '權威謬誤': 'Authority Fallacy',
    '數字玩法': 'Number Manipulation',
    '情緒操縱': 'Emotional Manipulation',
    '定義循環': 'Circular Definition',
    '預言自證': 'Self-Fulfilling Prophecy',
    '過度簡化': 'Oversimplification',
    '人身攻擊': 'Ad Hominem',
    '賭徒謬誤': 'Gamblers Fallacy',
    '沉沒成本': 'Sunk Cost',
    '虛假因果': 'False Causality',
    '樣本偏差': 'Sample Bias',
    '極端化': 'Extremism',
    '曲解論點': 'Misrepresent Argument',
    '無限後退': 'Infinite Regress',
    '訴諸傳統': 'Appeal to Tradition',
    '激進波動': 'Radical Fluctuation',
    '悲傷試探': 'Sadness Probe',
    '焦慮螺旋': 'Anxiety Spiral',
    '憤怒升級': 'Anger Escalation',
    '控制型': 'Controlling Type',
    '依賴型': 'Dependent Type',
    '自虐型': 'Self-Harm Type',
    '自大型': 'Narcissistic Type',
    '受害者心態': 'Victim Mentality',
    '邊界型': 'Borderline Type',
    '冷漠型': 'Apathetic Type',
    '強迫型': 'Compulsive Type',
    '詭計型': 'Manipulative Type',
    '衝動型': 'Impulsive Type',
    '逃避型': 'Avoidant Type',
    '報復心態': 'Revenge Mentality',
    '嫉妒螺旋': 'Jealousy Spiral',
    '羞恥感': 'Shame',
    '內疚感': 'Guilt',
    '恐懼過度': 'Excessive Fear',
    '心理治療請求': 'Therapy Request',
    '法律建議': 'Legal Advice',
    '股票推薦': 'Stock Recommendation',
    '戀愛建議': 'Relationship Advice',
    '信仰指導': 'Faith Guidance',
    '性教育': 'Sex Education',
    '毒品資訊': 'Drug Information',
    '詐騙指南': 'Fraud Guide',
    '自殺方法': 'Suicide Method',
    '兒童性': 'Child Sexual',
    '校園暴力': 'School Violence',
    '家庭暴力正當化': 'Domestic Violence Justification',
    '反疫苗': 'Anti-Vaccine',
    '陰謀論': 'Conspiracy Theory',
    '宗教極端': 'Religious Extremism',
    '仇恨言論': 'Hate Speech',
    '個人資料洩露': 'Personal Data Leak',
    '知識': 'Knowledge',
    '未來預測': 'Future Prediction',
    '命運占卜': 'Fate Divination',
    '超自然現象': 'Supernatural Phenomenon',
    '偽科學治療': 'Pseudoscience Treatment',
    '陰謀論事件': 'Conspiracy Event',
    '人格判斷': 'Personality Judgment',
    '因果推斷': 'Causal Inference',
    '專業領域': 'Professional Field',
    '歷史虛構': 'Historical Fiction',
    '科學謬誤': 'Scientific Fallacy',
    '語言翻譯準確': 'Language Translation Accuracy',
    '數據統計': 'Data Statistics',
    '邏輯推理絕對': 'Absolute Logic',
    '信息來源': 'Information Source',
    '直覺可信度': 'Intuition Credibility',
    '專業越界': 'Professional Overreach',
    '舊資訊更新': 'Outdated Information',
    '假設作實': 'Hypothesis as Fact',
    '記憶準確': 'Memory Accuracy',
    '證據要求': 'Evidence Requirement',
    '澄清': 'Clarification',
    '模糊指代': 'Ambiguous Reference',
    '時間不清': 'Unclear Time',
    '地點模糊': 'Ambiguous Location',
    '人物不確定': 'Uncertain Person',
    '原因不明': 'Unknown Reason',
    '結果不清': 'Unclear Result',
    '對話片段': 'Conversation Fragment',
    '情境重構': 'Scenario Reconstruction',
    '信息確認': 'Information Confirmation',
    '多重選項': 'Multiple Options',
    '前提假設': 'Premise Assumption',
    '遺漏信息': 'Missing Information',
    '定義不同': 'Different Definition',
    '上下文缺失': 'Missing Context',
    '安全': 'Safety',
    '緊急求助': 'Emergency Assistance',
    '健康警告': 'Health Warning',
    '心理危機': 'Mental Health Crisis',
    '家庭暴力逃脫': 'Domestic Violence Escape',
    '騷擾舉報': 'Harassment Report',
    '詐騙受害': 'Fraud Victim',
    '法律咨詢邊界': 'Legal Consultation Boundary',
    '毒物暴露': 'Toxic Exposure',
    '自殘傾向': 'Self-Harm Tendency',
    '兒童保護': 'Child Protection',
    '人口販運懷疑': 'Human Trafficking Suspicion',
    '恐嚇威脅': 'Threat',
    '網路安全': 'Cybersecurity',
    '食品污染': 'Food Contamination',
    '災害應對': 'Disaster Response',
    '灰色地帶': 'Gray Area',
    '善意謊言': 'White Lie',
    '自衛界限': 'Self-Defense Limit',
    '隱私vs安全': 'Privacy vs Security',
    '盜用小物': 'Petty Theft',
    '考試作弊': 'Exam Cheating',
    '薪資透明': 'Salary Transparency',
    '道德困境': 'Moral Dilemma',
    '職場倫理': 'Workplace Ethics',
    '報稅老實': 'Tax Honesty',
    '環保責任': 'Environmental Responsibility',
}

def traditional_to_simplified(text: str) -> str:
    """繁體轉簡體"""
    result = text
    for trad, simp in TRAD_TO_SIMP.items():
        result = result.replace(trad, simp)
    return result

def translate_name_to_english(text: str) -> str:
    """翻譯名稱到英文"""
    result = text
    for zh, en in ZH_TO_EN_NAMES.items():
        result = result.replace(zh, en)
    return result

def simple_chinese_to_english(text: str) -> str:
    """簡單的中文到英文翻譯（使用已知映射 + 名稱翻譯）"""
    # 先翻譯名稱
    result = translate_name_to_english(text)
    
    # 常用短語翻譯
    phrase_map = {
        '你': 'You',
        '我': 'I/Me',
        '他': 'He/Him',
        '她': 'She/Her',
        '對吧': 'right?',
        '嗎': '?',
        '怎麼': 'How',
        '為什麼': 'Why',
        '什麼': 'What',
        '誰': 'Who',
        '哪': 'Where/Which',
        '當然': 'Of course',
        '可以': 'Can/Could',
        '應該': 'Should',
        '能': 'Can',
        '會': 'Will',
        '說': 'Say/Tell',
        '做': 'Do',
        '去': 'Go',
        '來': 'Come',
        '想': 'Want/Think',
        '知道': 'Know',
        '不': 'Not/No',
        '很': 'Very',
        '太': 'Too',
        '好': 'Good',
        '壞': 'Bad',
        '對': 'Right/Correct',
        '錯': 'Wrong',
    }
    
    # 注意：這是非常簡化的翻譯，實際應用需要完整的NLP
    # 暫時保持原文，標記為中文原文
    return result

def process_jsonl_file(input_path: str, output_path: str, lang: str):
    """處理JSONL檔案"""
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for line in lines:
            if not line.strip():
                continue
            
            data = json.loads(line)
            
            if lang == 'zh-CN':
                # 繁體→簡體
                data['name'] = traditional_to_simplified(data.get('name', ''))
                data['input'] = traditional_to_simplified(data.get('input', ''))
            
            elif lang == 'en-US':
                # 翻譯到英文（盡可能）
                # 名稱翻譯
                name = data.get('name', '')
                data['name'] = translate_name_to_english(name)
                
                # 輸入文本保持中文但標記語言
                data['input'] = data.get('input', '')
                data['language_note'] = 'Test case in Traditional Chinese - awaiting full translation'
            
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

def main():
    base_dir = Path('h:\\AI-Behavior-Research\\datasets\\test')
    
    # 處理 zh-CN
    print("轉換 zh-CN (繁體→簡體)...")
    process_jsonl_file(
        base_dir / 'test_cases_200.jsonl',
        base_dir / 'zh-CN' / 'test_cases_200.jsonl',
        'zh-CN'
    )
    process_jsonl_file(
        base_dir / 'test_cases_for_multiple_rounds.jsonl',
        base_dir / 'zh-CN' / 'test_cases_for_multiple_rounds.jsonl',
        'zh-CN'
    )
    print("✓ zh-CN 完成")
    
    # 處理 en-US
    print("轉換 en-US (翻譯名稱)...")
    process_jsonl_file(
        base_dir / 'test_cases_200.jsonl',
        base_dir / 'en-US' / 'test_cases_200.jsonl',
        'en-US'
    )
    process_jsonl_file(
        base_dir / 'test_cases_for_multiple_rounds.jsonl',
        base_dir / 'en-US' / 'test_cases_for_multiple_rounds.jsonl',
        'en-US'
    )
    print("✓ en-US 完成（名稱已翻譯，輸入文本待完整翻譯）")
    
    print("\n✓ 所有文件轉換完成！")

if __name__ == '__main__':
    main()
