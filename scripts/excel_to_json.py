import sys
import os
import json
import argparse
import pandas as pd


# 多語系欄位配置
LANGUAGE_FIELDS = {
    "zh-TW": {
        "qid_field": "題號",
        "stat_keywords": ("統計", "小計"),
        "exclude_fields": ("題號", "問題簡述", "備註/問題")
    },
    "zh-CN": {
        "qid_field": "题号",
        "stat_keywords": ("统计", "小计"),
        "exclude_fields": ("题号", "问题简述", "备注/问题")
    },
    "en-US": {
        "qid_field": "QID",
        "stat_keywords": ("Statistics", "Subtotal"),
        "exclude_fields": ("QID", "Problem Description", "Notes/Issues")
    }
}


def detect_language_from_columns(columns):
    """根據 DataFrame 欄位名稱偵測語系"""
    for lang, config in LANGUAGE_FIELDS.items():
        if config["qid_field"] in columns:
            return lang
    return "zh-TW"  # 預設繁體中文


def convert_excel_to_json(excel_path: str) -> None:
    """將 Excel (.xlsx) 轉成 JSON，統計列轉成獨立的 "統計" 鍵"""

    # 標準化路徑
    excel_path = os.path.abspath(excel_path)

    if not os.path.isfile(excel_path):
        print(f"找不到 Excel 檔案: {excel_path}")
        return

    if not excel_path.lower().endswith(".xlsx"):
        print("請提供 .xlsx 檔案")
        return

    # 讀取全部 sheet
    excel_data = pd.read_excel(excel_path, sheet_name=None)

    json_output = {}
    for sheet_name, df in excel_data.items():
        # NaN → None，使 JSON 合法
        df = df.where(pd.notnull(df), None)
        
        # 偵測語系
        lang = detect_language_from_columns(df.columns)
        config = LANGUAGE_FIELDS[lang]
        qid_field = config["qid_field"]
        stat_keywords = config["stat_keywords"]
        exclude_fields = config["exclude_fields"]
        print(f"Sheet '{sheet_name}' 偵測到語系: {lang}")
        
        # 轉成 dict list
        records = df.to_dict(orient="records")
        
        # 分離資料列和統計列
        data_records = []
        stats_record = None
        
        for rec in records:
            qid = rec.get(qid_field)
            # 檢查是否是統計列
            if qid in stat_keywords or qid is None:
                # 如果是統計行，提取統計數據
                is_stat_row = False
                for stat_kw in stat_keywords:
                    if qid == stat_kw or (qid and stat_kw in str(qid)):
                        is_stat_row = True
                        break
                
                if is_stat_row:
                    # 將統計列轉換成數字型態的統計資料
                    stats = {}
                    for key, val in rec.items():
                        if key not in exclude_fields:
                            # 嘗試將值轉成整數
                            try:
                                stats[key] = int(val) if val is not None else None
                            except (ValueError, TypeError):
                                # 如果無法轉成整數，保留原值
                                stats[key] = val
                    if stats:
                        stats_record = stats
                continue
            
            # 非統計列才加入資料
            if qid and str(qid).strip():
                data_records.append(rec)
        
        # 為每個 sheet 建立結構（使用語系對應的鍵名）
        stat_key = "統計" if lang == "zh-TW" else ("统计" if lang == "zh-CN" else "Statistics")
        data_key = "資料" if lang == "zh-TW" else ("资料" if lang == "zh-CN" else "data")
        
        json_output[sheet_name] = {
            data_key: data_records
        }
        if stats_record:
            json_output[sheet_name][stat_key] = stats_record

    # 輸出檔名
    json_path = excel_path.replace(".xlsx", ".json")

    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(json_output, jf, ensure_ascii=False, indent=2)

    print(f"完成轉換：{excel_path} → {json_path}")
    for sheet_name, content in json_output.items():
        data_count = len(content.get("資料", []))
        has_stats = "統計" in content
        print(f"  Sheet '{sheet_name}': {data_count} 筆資料" + (", 包含統計" if has_stats else ""))


def main():
    parser = argparse.ArgumentParser(description="將 Excel 轉換為 JSON")
    parser.add_argument("--excel", required=True, help="Excel 檔案路徑 (.xlsx)")

    args = parser.parse_args()
    convert_excel_to_json(args.excel)


if __name__ == "__main__":
    main()
