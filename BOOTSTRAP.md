# Wenyan 自舉準備（`wenyan.wy`）

目前狀態：
- 已建立自舉入口與最小詞法骨架：`wenyan.wy`。
- 已有 `分詞`（最小可用版本），可掃描關鍵詞/數字/引言/單字名。
- 已加入測試 `tests/test_bootstrap_prep.py` 驗證：
  - `wenyan.wy` 可編譯且可執行。
  - `分詞` 可對最小示例產生 token 列。

## 里程碑

1. 詞法（Stage 1，進行中）
   - [x] 最小字元掃描與 token 輸出（`分詞`）
   - [ ] 對齊 `SPEC.md`：完整關鍵詞、字串跳脫、註釋/宏處理、錯誤定位

2. 文法（Stage 2）
   - 補齊最小語句集合：`吾有/今有`、`名之曰`、`施`、`乃得`、`書之`
   - 目標：輸出 Wenyan AST（先用簡化節點）

3. 轉譯（Stage 3）
   - 將 Stage 2 AST 轉為可執行中間表示
   - 先對齊最小子集，再逐步擴展

4. 自編譯（Stage 4）
   - 以 Python `wenyan.py` 編譯 `wenyan.wy`，產出可運行版本
   - 逐步削減對 Python 表達式逃逸的依賴

## 收斂準則

- `wenyan.wy` 可被現有 `wenyan.py` 編譯並運行。
- `wenyan.wy` 能解釋至少一個最小 Wenyan 程式。
- 新增語法/語義時，優先補對應測試。
