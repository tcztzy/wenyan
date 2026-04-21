# SPEC.md

## §G
G1. Wenyan.py 以 Python 3.10+、零 runtime 依賴實作文言：分詞、解析、轉 Python AST、執行、`.wy` 匯入、`wenyan`/`wywy` CLI。

## §C
C1. `pyproject.toml` `[project] dependencies` 必為空；新增標準庫 import 亦須有明確必要。
C2. 核心仍集於 `wenyan.py`；內部命名優先繁體中文，對外 API/CLI 名稱保持相容。
C3. Python 3.10 為最低可解析/可執行版本；tox `py310` 為底線。
C4. 行為改動須有 unittest；目標行覆蓋 100%，不得以大排除避之。
C5. 詞法/解析熱路須線性掃描、少分配；不得引入第三方 runtime。
C6. 涉 `wenyan.wy` 自舉語義者，須兼容本專案 `wenyan.py` 與 `@wenyan/cli`。

## §I
I.api. Python API：`詞法分析器`、`漢字數字/漢字變數字`、`解析`、`轉譯為PythonAST`、`編譯為PythonAST`、匯入鉤子、AST 節點、`文法之禍/文法錯誤`。
I.cli. `wenyan [--tokens|--wyast|--pyast|--no-outputHanzi] <檔案.wy|-> ...`；無參/`--help` 顯示說明。
I.wywy. `wywy` 以 `wenyan.wy` 解譯；可跑檔案、`-` stdin、自舉檔自身；失敗回傳 1。
I.import. `import wenyan` 安裝 `.wy` import hook；支援 `foo.wy` 與套件 `序.wy`；可安裝、卸載、顯式載入。
I.syntax. `wy.spec` 為語法鏡像；語法/關鍵字變更須同步。
I.ast. `AST_SPEC.md` 記錄 Wenyan AST 與 Python AST 轉譯準則。
I.lib. `lib/`、`lib/py/` 提供文言庫；一般搜尋當前目錄、`lib/py`、`lib`，`曆法` 優先根 `lib`。
I.bench. `scripts/wyperformance.py`、`scripts/benchmark_runtime_matrix.py`、`benchmark/` 結果/圖表為效能外部面。

## §V
V1. runtime 依賴恆空；包只發布 `wenyan.py`、`wenyan.wy`。
V2. `符號` 必含 `類别/值/位置`，並以 `type/value/position` 屬性兼容英文讀取。
V3. lexer 自左至右；優先序：言、忽略、名、關鍵詞、數、數據；關鍵詞最長匹配。
V4. token 位置為原文 `slice(start,end)`；keyword `值 is None`；`名/言/數/數據` 保值。
V5. 忽略符號為 `。 、 ， 矣 space tab LF CR 全角空格`；數據中遇忽略先切 token。
V6. 言以 `「「...」」` 或 `『...』`，可巢狀；輸出轉義 `"` 與 LF；雙引言後多一 `」` 視作字面值。
V7. 名以單 `「...」`；不巢狀；名未盡/言未盡/非法數皆拋 `文法之禍` 並帶檔名、行、列、行文。
V8. `漢字數字` 支援負號、`·`、`又`、大單位至 `極`、小數單位至 `漠`；大整數不得科學記號化。
V9. parser 產出繁體中文 dataclass AST；每節點有原文 `slice`。
V10. 宣告型別為 `數/言/爻/列/物/術/元`；預設值分別為 `0/""/False/[]/{}/lambda:0/None`，術定義須一術一名。
V11. 暫存棧：產值入棧；`其` 取頂並清棧；`書之` 輸出全棧後清；`噫` 清；多名由棧頂反向綁定。
V12. `取<n>`/`取其餘` 只供下一 `以施`；錯序報 `取後需以施`、`取後未以施`、`以施需先取`。
V13. 術支援 curry/partial；`其餘<型>` 參組須一名、只一次、居末，並以 list 收尾參。
V14. `施`/`以施`、`乃得/乃得矣/乃歸空無`、`加減乘除/所餘幾何`、`變`、`中有陽乎/中無陰乎` 須轉為等價 Python 語義。
V15. `若/若其然者/若其不然者/或若/若非` 支援比較、`之`、`之長`；`&&` 優先於 `||`。
V16. `恆為是`、`為是...遍`、`凡...中之`、`乃止`、`乃止是遍` 對應 while/for/break/continue；可由 return 收束。
V17. `昔之...今...是/是矣/是也` 支援名、下標、右下標與刪除；列為 1-based，越界讀 None，正向越界寫補 None，正向刪不擴列。
V18. `之其餘` 作 slice rest；`其` 作下標只求值一次。
V19. 匯入先找 `.wy`/`序.wy`，再 host Python；`方悟` 才導出名；循環匯入報 `循環匯入`。
V20. 宏 `或云/蓋謂` 於前處理展開；匯入宏遞迴收集；不得替換言字面量內文。
V21. `姑妄行此/如事不諧/豈...之禍歟/不知何禍歟/乃作罷` 與 `嗚呼...之禍` 對應 `文言之禍`。
V22. Python AST 不靠 `ast.fix_missing_locations`；所有可定位 stmt/expr/excepthandler 具合法四位置欄。
V23. `--no-outputHanzi` 以阿拉伯數/兼容格式輸出；列單行/多行與 100 項截斷行為穩定。
V24. import hook 安裝卸載冪等；`import wenyan` 後 `.wy` 模組可被 Python 正常 import/from import。
V25. `wenyan.wy` 可編譯可執行；自舉分詞/文法/解譯子集與 host 測例同步推進。
V26. `examples/*.wy` 全部作回歸；benchmark 腳本比較輸出與圖表生成須可測。

## §T
id|status|task|cites
T1|x|補齊 `wenyan.wy` 詞法與 host lexer 齊：字串跳脫、註釋/宏處理、錯誤定位|V3,V4,V6,V7,V20,V25,I.wywy
T2|x|補齊 `wenyan.wy` 文法/解譯：賦值邊界、容器、完整數值語義、其餘語法|V8,V12,V13,V17,V18,V25,I.wywy
T3|x|將 100% 行覆蓋門禁固化為標準庫 trace 或等價 CI 檢查|C4,V26
T4|.|語法/關鍵字/語義變更時同步 `wy.spec`、`AST_SPEC.md`、示例、雙端自舉回歸|C6,I.syntax,I.ast,V25,V26
T5|.|釐清並測定條件式完整語法與 JS-only 標準庫 Python 等價策略|I.ast,V15,V19

## §B
id|date|cause|fix
