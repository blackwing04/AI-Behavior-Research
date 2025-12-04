import json
import sys
import argparse
import os
from openpyxl import load_workbook


def write_json_to_excel(excel_path: str, json_path: str) -> None:
    """讀 JSON 並寫入既有 Excel"""

    # 路徑標準化處理
    excel_path = os.path.abspath(excel_path)
    json_path = os.path.abspath(json_path)

    if not os.path.isfile(excel_path):
        print(f"找不到 Excel 檔案: {excel_path}")
        return

    if not os.path.isfile(json_path):
        print(f"找不到 JSON 檔案: {json_path}")
        return

    # （目前不建立備份，輸出為新檔案 _output.xlsx）

    # 載入 JSON（更健壯的辨識：支援 dict 包含 list、list of json-strings）
    with open(json_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # 決定要遍歷的資料清單
    data_list = None
    if isinstance(json_data, dict):
        # 常見情況：根物件有一個 key 對應到 list（例如 "整理後"）
        for k, v in json_data.items():
            if isinstance(v, list) and len(v) > 0 and all(isinstance(x, dict) for x in v[:10]):
                data_list = v
                break
        # 若 dict 的每個 value 都是 dict，轉成 list
        if data_list is None and all(isinstance(v, dict) for v in json_data.values()):
            data_list = list(json_data.values())
    elif isinstance(json_data, list):
        # list 可能是 list of dicts 或 list of json-strings
        if len(json_data) > 0 and all(isinstance(x, str) for x in json_data[:10]):
            parsed = []
            for s in json_data:
                try:
                    parsed.append(json.loads(s))
                except Exception:
                    # 無法解析的字串就跳過
                    continue
            data_list = parsed
        else:
            data_list = json_data

    if data_list is None:
        print("無法判別 JSON 結構（找不到可用的 list of dicts）")
        return

    # 載入 Excel
    wb = load_workbook(excel_path)
    ws = wb.active

    # 找欄位
    headers = {}
    for col in range(1, ws.max_column + 1):
        key = ws.cell(row=1, column=col).value
        if key:
            headers[key] = col

    required_fields = [
        "題號", "is_reject", "is_request_info", "is_clarify",
        "is_allow_risk", "is_contradict", "is_deny",
        "is_invalid", "need_fix", "備註/問題"
    ]

    for field in required_fields:
        if field not in headers:
            print(f"Excel 缺少欄位: {field}")
            return

    # 寫入資料
    for item in data_list:
        if not isinstance(item, dict):
            continue
        # 支援多種題號欄位命名
        qid = item.get("題號") or item.get("qid") or item.get("QID") or item.get("qID")
        if not qid:
            continue

        target_row = None
        for row in range(2, ws.max_row + 1):
            cell_val = ws.cell(row=row, column=headers["題號"]).value
            if cell_val is None:
                continue
            if str(cell_val).strip() == str(qid).strip():
                target_row = row
                break

        if not target_row:
            print(f"題號 {qid} 找不到，略過")
            continue

        for key, value in item.items():
            if key in headers:
                ws.cell(row=target_row, column=headers[key]).value = value

    # 自動輸出
    output_path = excel_path.replace(".xlsx", "_output.xlsx")

    wb.save(output_path)
    print(f"完成：資料已寫入 {output_path}")


def main():
    parser = argparse.ArgumentParser(description="將 JSON 寫入 Excel")
    parser.add_argument("--excel", required=True, help="Excel 模板檔案路徑")
    parser.add_argument("--json", required=True, help="JSON 資料檔案路徑")

    args = parser.parse_args()
    write_json_to_excel(args.excel, args.json)


if __name__ == "__main__":
    main()
