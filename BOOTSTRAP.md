# Wenyan 自舉準備（`wenyan.wy`）

目前狀態：
- 已建立自舉入口骨架：`wenyan.wy`。
- 目前骨架只保留 `主術` 與分階段佔位，尚未實作編譯流程。

## 里程碑

1. 詞法（Stage 1）
   - 在 `wenyan.wy` 內重寫最小可用詞法分析。
   - 目標：可把一段 Wenyan 源碼切成 token 序列。

2. 文法（Stage 2）
   - 補齊最小語句集合：`吾有/今有`、`名之曰`、`施`、`乃得`、`書之`。
   - 目標：輸出 Wenyan AST（可先用簡化節點）。

3. 轉譯（Stage 3）
   - 將 Stage 2 AST 轉為可執行中間表示。
   - 先對齊最小子集，再逐步擴展。

4. 自編譯（Stage 4）
   - 以 Python `wenyan.py` 編譯 `wenyan.wy`，產出可運行版本。
   - 逐步削減對 Python 表達式逃逸的依賴。

## 收斂準則

- `wenyan.wy` 可被現有 `wenyan.py` 編譯並運行。
- `wenyan.wy` 能解釋至少一個最小 Wenyan 程式。
- 新增語法/語義時，優先補對應測試。
