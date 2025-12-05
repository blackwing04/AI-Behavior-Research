# write_json_to_excel.py 修復說明

## 問題診斷

### 原始問題
執行命令後沒有將 JSON 資料轉換到 Excel，程式在尋找可轉換的資料時失敗了。

```bash
python scripts\write_json_to_excel.py --excel "Base分析統計表.xlsx" --json "Base分析統計表.json"
```

### 根本原因

JSON 檔案的結構為：
```json
{
  "整理後": {
    "資料": [
      { "qid": "Q001", ... },
      { "qid": "Q002", ... },
      ...
    ]
  }
}
```

但原始程式的資料提取邏輯無法處理**深層嵌套的 list**：

```python
# 原始邏輯 (錯誤)
if isinstance(json_data, dict):
    for k, v in json_data.items():
        if isinstance(v, list):  # ← 尋找直接的 list
            data_list = v
            break
    # 如果找不到，就把 dict values 轉成 list
    if data_list is None and all(isinstance(v, dict) for v in json_data.values()):
        data_list = list(json_data.values())  # ← [{ "資料": [...] }]
```

**執行流程分析：**
1. `json_data = { "整理後": {...} }` (dict)
2. 第一個 value 是 `{ "資料": [...] }` (dict，不是 list)
3. 第一層 if 不符合
4. 執行第二個 if：所有 values 都是 dict → `true`
5. `data_list = list(json_data.values())` = `[{ "資料": [...] }]`
6. 這是一個只有 1 個元素的 list，該元素是 dict，不是 dict 的 list
7. **資料提取失敗**

## 修復方案

### 核心改進：遞迴深層搜索

新增遞迴函數 `find_data_list()`，可以深層搜索並找到真正的資料 list：

```python
def find_data_list(obj, depth=0):
    """遞迴搜尋可用的 list of dicts"""
    if depth > 5:  # 防止無限遞迴
        return None
    
    if isinstance(obj, list):
        # 情況 1: list of dicts ✓
        if len(obj) > 0 and all(isinstance(x, dict) for x in obj[:10]):
            return obj
        # 情況 2: list of json-strings (支援舊格式)
        if len(obj) > 0 and all(isinstance(x, str) for x in obj[:10]):
            parsed = [json.loads(s) for s in obj if can_parse(s)]
            if parsed and all(isinstance(x, dict) for x in parsed[:10]):
                return parsed
    
    elif isinstance(obj, dict):
        # 情況 3: dict 包含直接的 list
        for k, v in obj.items():
            if isinstance(v, list) and is_list_of_dicts(v):
                return v
        
        # 情況 4: 遞迴進入 dict values（找深層的 list）
        for k, v in obj.items():
            if isinstance(v, dict):
                result = find_data_list(v, depth + 1)
                if result is not None:
                    return result
    
    return None
```

### 其他改進

1. **更寬鬆的欄位驗證**
   - 原先：要求所有必要欄位都存在 → 容易失敗
   - 改善：只要求 "題號" + 至少 1 個分類欄位
   - 缺少的欄位會提示警告，但不中斷執行

2. **改進錯誤提示**
   - 新增 `written_count` 變數追蹤
   - 最終輸出顯示實際寫入的筆數
   - 缺少的欄位會列出來提示

## 修復後的效果

### 測試結果
```bash
$ python scripts\write_json_to_excel.py --excel "Base分析統計表.xlsx" --json "Base分析統計表.json"
完成：已寫入 180 筆資料到 h:\...\Base分析統計表_output.xlsx
```

✅ **成功識別到 JSON 結構中的 180 筆資料**
✅ **全部寫入 Excel 檔案**
✅ **生成輸出檔案 `Base分析統計表_output.xlsx`**

## 支援的 JSON 格式

修復後的程式現在支援以下 JSON 結構：

### 格式 1：深層嵌套（新增支援）
```json
{
  "整理後": {
    "資料": [...]
  }
}
```

### 格式 2：直接 list
```json
[
  { "qid": "Q001", ... },
  ...
]
```

### 格式 3：淺層嵌套
```json
{
  "data": [...]
}
```

### 格式 4：list of JSON strings（舊格式相容）
```json
[
  "{\"qid\": \"Q001\", ...}",
  ...
]
```

## 使用建議

對於不同的 JSON 結構，程式會自動適配：

```bash
# V4 分析統計表 (深層嵌套)
python scripts\write_json_to_excel.py \
  --excel "test_logs\V4\V4分析統計表.xlsx" \
  --json "test_logs\V4\V4分析統計表.json"

# Base 分析統計表 (深層嵌套)
python scripts\write_json_to_excel.py \
  --excel "test_logs\base_model\Base分析統計表.xlsx" \
  --json "test_logs\base_model\Base分析統計表.json"

# 標準 list 格式的 JSON
python scripts\write_json_to_excel.py \
  --excel "output.xlsx" \
  --json "standard_data.json"
```

## 程式碼檔案位置

📝 修改檔案：`scripts/write_json_to_excel.py`

### 修改的函數
- `find_data_list()` - 新增遞迴搜索函數
- `write_json_to_excel()` - 改進 JSON 結構辨識與欄位驗證

### 修改行數
- 舊邏輯：~30 行（簡單但不夠完善）
- 新邏輯：~70 行（遞迴深層搜索 + 寬鬆驗證）

---

**修復日期**: 2025-12-05
**測試通過**: ✅ Base分析統計表.json (180 筆資料)
