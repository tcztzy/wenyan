# -*- coding: utf-8 -*-
"""Wenyan（文言）語言的 Python 實作。

目前包含：
  - 詞法分析（`詞法分析器`）
  - 文言數字轉換（`漢字數字`）
  - Wenyan AST（語法樹）與 Python AST 轉譯（見 `AST_SPEC.md`）
"""

from __future__ import annotations

import ast
import keyword
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple

__all__ = [
    "詞法分析器",
    "漢字數字",
    "漢字變數字",
    "主術",
    "符號",
    "文法之禍",
    "文法錯誤",
    # AST / 轉譯（MVP）
    "程式",
    "句",
    "值",
    "名值",
    "言值",
    "數值",
    "爻值",
    "其值",
    "其餘值",
    "宣告句",
    "初始化句",
    "命名句",
    "匯入句",
    "術參數",
    "術定義句",
    "施句",
    "以施句",
    "取句",
    "返回句",
    "列充句",
    "列銜句",
    "物屬性",
    "物定義句",
    "書之句",
    "噫句",
    "算術句",
    "變句",
    "夫句",
    "之句",
    "之長句",
    "昔今句",
    "若句",
    "恆為是句",
    "為是遍句",
    "乃止句",
    "乃止是遍句",
    "凡句",
    "試句",
    "捕捉子句",
    "擲句",
    "註釋句",
    "宏句",
    "文法分析器",
    "解析",
    "轉譯為PythonAST",
    "編譯為PythonAST",
]
版本號 = "0.1.0"

忽略符號 = frozenset({"。", "、", "，", "矣", " ", "\t", "\n", "\r", "　"})

數字對照: Dict[str, int] = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}

小單位: Dict[str, int] = {"十": 10, "百": 100, "千": 1000}

大單位: Dict[str, int] = {
    "萬": 10**4,
    "億": 10**8,
    "兆": 10**12,
    "京": 10**16,
    "垓": 10**20,
    "秭": 10**24,
    "穰": 10**28,
    "溝": 10**32,
    "澗": 10**36,
    "正": 10**40,
    "載": 10**44,
    "極": 10**48,
}

小數單位序: Dict[str, int] = {
    "分": 1,
    "釐": 2,
    "毫": 3,
    "絲": 4,
    "忽": 5,
    "微": 6,
    "纖": 7,
    "沙": 8,
    "塵": 9,
    "埃": 10,
    "渺": 11,
    "漠": 12,
}

數值字符 = frozenset(
    "負·又零〇一二三四五六七八九十百千萬億兆京垓秭穰溝澗正載極分釐毫絲忽微纖沙塵埃渺漠"
)

關鍵詞: list[str] = [
    "吾有",
    "今有",
    "物之",
    "有",
    "數",
    "列",
    "言",
    "術",
    "爻",
    "物",
    "元",
    "書之",
    "名之曰",
    "施",
    "以施",
    "曰",
    "噫",
    "取",
    "昔之",
    "今",
    "是矣",
    "是也",
    "不復存矣",
    "其",
    "乃得",
    "乃得矣",
    "乃歸空無",
    "是謂",
    "之術也",
    "必先得",
    "是術曰",
    "乃行是術曰",
    "欲行是術",
    "也",
    "云云",
    "凡",
    "中之",
    "恆為是",
    "為是",
    "遍",
    "乃止",
    "乃止是遍",
    "若非",
    "若",
    "者",
    "若其然者",
    "若其不然者",
    "或若",
    "其物如是",
    "之物也",
    "夫",
    "等於",
    "不等於",
    "不大於",
    "不小於",
    "大於",
    "小於",
    "加",
    "減",
    "乘",
    "除",
    "中有陽乎",
    "中無陰乎",
    "變",
    "所餘幾何",
    "以",
    "於",
    "之長",
    "之",
    "充",
    "銜",
    "其餘",
    "陰",
    "陽",
    "吾嘗觀",
    "中",
    "之書",
    "方悟",
    "之義",
    "嗚呼",
    "之禍",
    "姑妄行此",
    "如事不諧",
    "豈",
    "之禍歟",
    "不知何禍歟",
    "乃作罷",
    "或云",
    "蓋謂",
    "注曰",
    "疏曰",
    "批曰",
]

關鍵詞依長度 = sorted(關鍵詞, key=len, reverse=True)
關鍵詞前綴: Dict[str, List[str]] = {}
for 詞 in 關鍵詞依長度:
    關鍵詞前綴.setdefault(詞[0], []).append(詞)  # ty:ignore[invalid-argument-type, not-subscriptable]


class 文法之禍(SyntaxError):
    """文法錯誤。

    Args:
        訊息: 錯誤訊息。
        位置: 錯誤位置資訊（SyntaxError 兼容格式）。
    """

    ...


文法錯誤 = 文法之禍


@dataclass(frozen=True)
class 符號:
    """詞法單元。"""

    類别: str
    值: str | None
    位置: slice

    @property
    def position(self) -> slice:
        return self.位置

    @property
    def type(self) -> str:
        return self.類别

    @property
    def value(self) -> str | None:
        return self.值


@dataclass
class 詞法分析器:
    """詞法分析器。"""

    內容: str
    文檔名: str = "<言>"

    def __iter__(self) -> Iterator[符號]:
        內容 = self.內容
        長度 = len(內容)
        索引 = 0
        數據起點: int | None = None
        while 索引 < 長度:
            if 內容.startswith("「「", 索引) or 內容.startswith("『", 索引):
                if 數據起點 is not None:
                    yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))
                    數據起點 = None
                文字, 結束 = self._讀言(索引)
                if 內容.startswith("「「", 索引) and 結束 < 長度 and 內容[結束] == "」":
                    # 與 @wenyan/cli 對齊：雙引言後緊接額外「」時，尾「」視為字面值。
                    結束 += 1
                    文字 += "」"
                yield 符號("言", 文字, slice(索引, 結束))
                索引 = 結束
                continue

            字 = 內容[索引]
            if 字 in 忽略符號:
                if 數據起點 is not None:
                    yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))
                    數據起點 = None
                索引 += 1
                continue

            if 字 == "「":
                if 數據起點 is not None:
                    yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))
                    數據起點 = None
                名稱, 結束 = self._讀名(索引)
                yield 符號("名", 名稱, slice(索引, 結束))
                索引 = 結束
                continue

            關鍵 = self._匹配關鍵詞(索引)
            if 關鍵 is not None:
                if 數據起點 is not None:
                    yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))
                    數據起點 = None
                結束 = 索引 + len(關鍵)
                yield 符號(關鍵, None, slice(索引, 結束))
                索引 = 結束
                continue

            if 字 in 數值字符:
                if 數據起點 is not None:
                    yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))
                    數據起點 = None
                開始 = 索引
                索引 += 1
                while 索引 < 長度 and 內容[索引] in 數值字符:
                    索引 += 1
                片段 = 內容[開始:索引]
                try:
                    數字字串 = 漢字數字(片段)
                except 文法之禍:
                    self._拋出語法錯誤("非法數", 開始)
                yield 符號("數", 數字字串, slice(開始, 索引))
                continue

            if 數據起點 is None:
                數據起點 = 索引
            索引 += 1

        if 數據起點 is not None:
            yield 符號("數據", 內容[數據起點:索引], slice(數據起點, 索引))

    def _匹配關鍵詞(self, 索引: int) -> str | None:
        內容 = self.內容
        候選 = 關鍵詞前綴.get(內容[索引])
        if not 候選:
            return None
        for 詞 in 候選:
            if 內容.startswith(詞, 索引):
                return 詞
        return None

    def _讀言(self, 起點: int) -> Tuple[str, int]:
        內容 = self.內容
        索引 = 起點
        內容片段: List[str] = []
        層級 = 0
        while 索引 < len(內容):
            字 = 內容[索引]
            if 字 == "「":
                層級 += 1
            elif 字 == "」":
                層級 -= 1
            elif 字 == "『":
                層級 += 2
            elif 字 == "』":
                層級 -= 2
            內容片段.append(字)
            索引 += 1
            if 層級 == 0:
                文字 = "".join(內容片段)
                if 文字.startswith("「"):
                    文字 = 文字[2:]
                else:
                    文字 = 文字[1:]
                if 文字.endswith("」"):
                    文字 = 文字[:-2]
                else:
                    文字 = 文字[:-1]
                文字 = 文字.replace('"', '\\"').replace("\n", "\\n")
                return 文字, 索引
        self._拋出語法錯誤("言未尽", 起點)
        raise AssertionError("unreachable")

    def _讀名(self, 起點: int) -> Tuple[str, int]:
        內容 = self.內容
        索引 = 起點 + 1
        內容片段: List[str] = []
        while 索引 < len(內容):
            if 內容[索引] == "」":
                索引 += 1
                return "".join(內容片段), 索引
            內容片段.append(內容[索引])
            索引 += 1
        self._拋出語法錯誤("名未尽", 起點)
        raise AssertionError("unreachable")

    def _拋出語法錯誤(self, 訊息: str, 索引: int) -> None:
        行號, 列偏移, 行文字 = 計算行列(self.內容, 索引)
        raise 文法之禍(訊息, (self.文檔名, 行號, 列偏移, 行文字))


def 計算行列(內容: str, 索引: int) -> Tuple[int, int, str]:
    """計算行號、列偏移與行文字。

    Args:
        內容: 原始文字。
        索引: 0-based 索引。

    Returns:
        (行號, 列偏移, 行文字)。
    """

    行首 = 內容.rfind("\n", 0, 索引)
    if 行首 == -1:
        行首 = 0
        行號 = 1
    else:
        行首 += 1
        行號 = 內容.count("\n", 0, 行首) + 1
    行末 = 內容.find("\n", 索引)
    if 行末 == -1:
        行末 = len(內容)
    列偏移 = 索引 - 行首 + 1
    行文字 = 內容[行首:行末]
    return 行號, 列偏移, 行文字


def 漢字數字(漢字數: str) -> str:
    """將文言數字轉成十進位字串。

    Args:
        漢字數: 文言數字字串。

    Returns:
        十進位字串（必要時含小數點）。

    Raises:
        語法錯誤: 若字串不是合法數字。
    """

    if not 漢字數:
        raise 文法之禍("空數字")
    if any(字 not in 數值字符 for 字 in 漢字數):
        raise 文法之禍("非數值字符")

    負號 = False
    if 漢字數.startswith("負"):
        負號 = True
        漢字數 = 漢字數[1:]
        if "負" in 漢字數:
            raise 文法之禍("多重負號")
    elif "負" in 漢字數:
        raise 文法之禍("負號位置錯誤")

    if not 漢字數:
        raise 文法之禍("空數字")

    if "·" in 漢字數:
        if 漢字數.count("·") != 1:
            raise 文法之禍("多重小數點")
        if "又" in 漢字數:
            raise 文法之禍("混用小數點與又")
        for 字 in 漢字數:
            if 字 == "·":
                continue
            if 字 not in 數字對照:
                raise 文法之禍("非數字")
        if 漢字數.startswith("·") or 漢字數.endswith("·"):
            raise 文法之禍("小數點位置錯誤")
        整數部, 小數部 = 漢字數.split("·", 1)
        整數數字 = "".join(str(數字對照[字]) for 字 in 整數部) if 整數部 else "0"
        小數數字 = "".join(str(數字對照[字]) for 字 in 小數部)
        整數數字 = 整數數字.lstrip("0") or "0"
        結果 = 整數數字 if not 小數數字 else f"{整數數字}.{小數數字}"
        return f"-{結果}" if 負號 else 結果

    if "又" in 漢字數:
        if 漢字數.count("又") != 1:
            raise 文法之禍("多重又")
        整數部, 尾部 = 漢字數.split("又", 1)
        if not 尾部:
            raise 文法之禍("又後為空")
        整數值 = 解析整數(整數部) if 整數部 else 0
        if any(字 in 小數單位序 for 字 in 尾部):
            小數數字 = 解析小數(尾部)
            if not 小數數字 or set(小數數字) == {"0"}:
                結果 = str(整數值)
            else:
                結果 = f"{整數值}.{小數數字}"
        else:
            尾值 = 解析整數(尾部)
            結果 = str(整數值 + 尾值)
        return f"-{結果}" if 負號 else 結果

    if any(字 in 小數單位序 for 字 in 漢字數):
        小數數字 = 解析小數(漢字數)
        if not 小數數字 or set(小數數字) == {"0"}:
            結果 = "0"
        else:
            結果 = f"0.{小數數字}"
        return f"-{結果}" if 負號 else 結果

    整數值 = 解析整數(漢字數)
    結果 = str(整數值)
    return f"-{結果}" if 負號 else 結果


漢字變數字 = 漢字數字


def 解析整數(漢字數: str) -> int:
    """解析整數部分。

    Args:
        漢字數: 整數字串。

    Returns:
        整數值。

    Raises:
        語法錯誤: 若格式不合法。
    """

    if not 漢字數:
        return 0
    if any(字 in 小數單位序 for 字 in 漢字數) or "·" in 漢字數 or "又" in 漢字數:
        raise 文法之禍("非法整數")
    if all(字 in 數字對照 for 字 in 漢字數):
        數字字串 = "".join(str(數字對照[字]) for 字 in 漢字數)
        return int(數字字串) if 數字字串 else 0

    總和 = 0
    節值 = 0
    當前數 = 0
    有數 = False
    for 字 in 漢字數:
        if 字 in 數字對照:
            當前數 = 數字對照[字]
            有數 = True
        elif 字 in 小單位:
            單位 = 小單位[字]
            if not 有數:
                當前數 = 1
            節值 += 當前數 * 單位
            當前數 = 0
            有數 = False
        elif 字 in 大單位:
            單位 = 大單位[字]
            if not 有數 and 節值 == 0:
                節值 = 1
            else:
                節值 += 當前數
            總和 += 節值 * 單位
            節值 = 0
            當前數 = 0
            有數 = False
        else:
            raise 文法之禍("非法整數")
    return 總和 + 節值 + (當前數 if 有數 else 0)


def 解析小數(漢字數: str) -> str:
    """解析小數部分並回傳小數位字串。

    Args:
        漢字數: 小數字串。

    Returns:
        小數位字串。

    Raises:
        語法錯誤: 若格式不合法。
    """

    if not 漢字數:
        raise 文法之禍("空小數")
    位序 = 小數單位序
    下一位 = 1
    位數: List[str] = []
    索引 = 0
    while 索引 < len(漢字數):
        字 = 漢字數[索引]
        if 字 in 數字對照:
            數字 = 數字對照[字]
            if 索引 + 1 < len(漢字數) and 漢字數[索引 + 1] in 位序:
                單位字 = 漢字數[索引 + 1]
                目標位 = 位序[單位字]
                if 目標位 < 下一位:
                    raise 文法之禍("小數位錯序")
                while 下一位 < 目標位:
                    位數.append("0")
                    下一位 += 1
                位數.append(str(數字))
                下一位 = 目標位 + 1
                索引 += 2
            else:
                if 下一位 > 12:
                    raise 文法之禍("小數位過長")
                位數.append(str(數字))
                下一位 += 1
                索引 += 1
        elif 字 in 位序:
            目標位 = 位序[字]
            if 目標位 < 下一位:
                raise 文法之禍("小數位錯序")
            while 下一位 < 目標位:
                位數.append("0")
                下一位 += 1
            位數.append("1")
            下一位 = 目標位 + 1
            索引 += 1
        else:
            raise 文法之禍("非法小數")
    return "".join(位數)


# ---------------------------------------------------------------------------
# Wenyan AST（MVP）
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class 節點:
    """語法樹節點基類。

    Args:
        位置: 對應原始碼片段的 `slice(start, end)`，用於錯誤定位。
    """

    位置: slice


@dataclass(frozen=True)
class 值(節點):
    """值（表達式）基類。"""


@dataclass(frozen=True)
class 名值(值):
    """名（identifier）。"""

    名: str


@dataclass(frozen=True)
class 言值(值):
    """言（字面量字串）。

    注意：`文` 為 lexer 產出的「已做最小轉義」內容（例如 `\\n`、`\\"`），
    轉譯成 Python `ast.Constant` 時需還原成真實字元。
    """

    文: str


@dataclass(frozen=True)
class 數值(值):
    """數（數值字面量）。"""

    文: str


@dataclass(frozen=True)
class 爻值(值):
    """爻（陰/陽）。"""

    真: bool


@dataclass(frozen=True)
class 其值(值):
    """其（暫存棧頂）。"""


@dataclass(frozen=True)
class 其餘值(值):
    """其餘（容器下標語法中的 REST）。"""


@dataclass(frozen=True)
class 句(節點):
    """語句基類。"""


@dataclass(frozen=True)
class 程式(節點):
    """程式根節點。"""

    句列: list[句]


@dataclass(frozen=True)
class 宣告句(句):
    """變數宣告（`吾有/今有`）。"""

    數量: int
    類型: str
    初值列: list[值]
    名列: list[str]
    公開: bool


@dataclass(frozen=True)
class 初始化句(句):
    """初始化宣告（`有`）。"""

    類型: str
    初值: 值
    名: str | None


@dataclass(frozen=True)
class 命名句(句):
    """命名（`名之曰`；從暫存棧取值）。"""

    名列: list[str]


@dataclass(frozen=True)
class 匯入句(句):
    """匯入（`吾嘗觀 ... 之書 ... 方悟 ... 之義`）。"""

    模組: str
    名列: list[str]


@dataclass(frozen=True)
class 術參數(節點):
    """術參數。"""

    名: str
    類型: str
    其餘: bool = False


@dataclass(frozen=True)
class 術定義句(句):
    """術定義（函數）。"""

    名: str
    參數列: list[術參數]
    體: list[句]
    公開: bool


@dataclass(frozen=True)
class 施句(句):
    """呼叫（`施 <術> 於 <值>...`）。"""

    術: 值
    參數列: list[值]


@dataclass(frozen=True)
class 以施句(句):
    """呼叫（`以施 <術>`）。"""

    術: 值


@dataclass(frozen=True)
class 取句(句):
    """取參數（`取 <數>` / `取其餘`）。"""

    數量: int | None
    其餘: bool = False


@dataclass(frozen=True)
class 返回句(句):
    """返回（`乃得/乃得矣/乃歸空無`）。"""

    值: 值 | None
    取棧: bool
    空無: bool


@dataclass(frozen=True)
class 列充句(句):
    """列追加（`充`）。"""

    列: 值
    值列: list[值]


@dataclass(frozen=True)
class 列銜句(句):
    """列/言銜接（`銜`）。"""

    列: 值
    列列: list[值]


@dataclass(frozen=True)
class 物屬性(節點):
    """物屬性（`物之...者`）。"""

    鍵: 言值
    類型: str
    值: 值


@dataclass(frozen=True)
class 物定義句(句):
    """物定義（`其物如是 ... 是謂 ... 之物也`）。"""

    名: str
    屬性列: list[物屬性]


@dataclass(frozen=True)
class 書之句(句):
    """輸出（`書之`）。"""


@dataclass(frozen=True)
class 噫句(句):
    """清空暫存棧（`噫`）。"""


@dataclass(frozen=True)
class 算術句(句):
    """二元運算（含算術/餘數/邏輯）。"""

    算: str
    左: 值
    右: 值


@dataclass(frozen=True)
class 變句(句):
    """一元運算（`變`）。"""

    值: 值


@dataclass(frozen=True)
class 夫句(句):
    """取值入棧（`夫 <值>`）。"""

    值: 值


@dataclass(frozen=True)
class 之句(句):
    """下標取值（`夫 <容器> 之 <索引>`）。"""

    容器: 值
    索引: 值


@dataclass(frozen=True)
class 之長句(句):
    """取長度（`夫 <容器> 之長`）。"""

    容器: 值


@dataclass(frozen=True)
class 昔今句(句):
    """賦值或刪除（`昔之...者 今 ... 是矣` / `... 不復存矣`）。"""

    左名: str
    左下標: 值 | None
    右值: 值 | None
    右下標: 值 | None
    刪除: bool


@dataclass(frozen=True)
class 條件原子(節點):
    """條件式中的原子（值 + 可選後綴）。"""

    值: 值
    下標: 值 | None
    之長: bool


@dataclass(frozen=True)
class 或若子句(節點):
    """`或若` 子句。"""

    條件: list[條件原子 | str]
    體: list[句]


@dataclass(frozen=True)
class 若句(句):
    """若（if/elif/else）。"""

    條件: list[條件原子 | str]
    反轉: bool
    然: list[句]
    另若列: list[或若子句]
    否則: list[句]


@dataclass(frozen=True)
class 恆為是句(句):
    """無條件循環（`恆為是 ... 云云/也`）。"""

    體: list[句]


@dataclass(frozen=True)
class 為是遍句(句):
    """次數循環（`為是 <次數> 遍 ... 云云/也`）。"""

    次數: 值
    體: list[句]


@dataclass(frozen=True)
class 乃止句(句):
    """break（`乃止`）。"""


@dataclass(frozen=True)
class 乃止是遍句(句):
    """continue（`乃止是遍`）。"""


@dataclass(frozen=True)
class 凡句(句):
    """遍歷（`凡 ... 中之 ...`）。"""

    容器: 值
    變數名: str
    體: list[句]


@dataclass(frozen=True)
class 捕捉子句(節點):
    """捕捉子句。"""

    錯名: 值 | None
    變數名: str | None
    體: list[句]
    亦可: bool


@dataclass(frozen=True)
class 試句(句):
    """異常處理（`姑妄行此`）。"""

    體: list[句]
    捕捉列: list[捕捉子句]


@dataclass(frozen=True)
class 擲句(句):
    """拋出（`嗚呼 ... 之禍`）。"""

    名: 值
    訊: 值 | None


@dataclass(frozen=True)
class 註釋句(句):
    """註釋（`注曰/疏曰/批曰`）。"""

    文: str


@dataclass(frozen=True)
class 宏句(句):
    """宏定義（`或云/蓋謂`）。"""

    模式: str
    置換: str


@dataclass(frozen=True)
class 宏定義:
    """宏定義（預處理用）。"""

    模式: str
    置換: str
    正則: re.Pattern
    占位列: list[str]


@dataclass
class 編譯環境:
    """編譯過程共用快取。"""

    根目錄: str
    模組快取: dict[str, list[ast.stmt]]
    宏快取: dict[str, list[宏定義]]
    源碼快取: dict[str, str]
    宏解析中: set[str]
    編譯中: set[str]
    已載入: set[str]


內建型別詞 = frozenset({"數", "列", "言", "爻", "物", "術", "元"})
比較詞對照 = {
    "等於": "==",
    "不等於": "!=",
    "不大於": "<=",
    "不小於": ">=",
    "大於": ">",
    "小於": "<",
}
邏輯詞對照 = {"中有陽乎": "||", "中無陰乎": "&&"}


class 文法分析器:
    """將 `詞法分析器` 的輸出轉為 Wenyan AST。"""

    def __init__(self, 內容: str, 文檔名: str = "<言>") -> None:
        self.內容 = 內容
        self.文檔名 = 文檔名
        self.符號列 = list(詞法分析器(內容, 文檔名))
        self._索引 = 0

    def 解析程式(self) -> 程式:
        """解析整個程式。"""

        起點 = 0
        句列 = self._解析語句列(終止詞=frozenset())
        終點 = len(self.內容)
        return 程式(slice(起點, 終點), 句列)

    # ---- 基礎操作 -----------------------------------------------------

    def _到尾(self) -> bool:
        return self._索引 >= len(self.符號列)

    def _看(self) -> 符號 | None:
        if self._到尾():
            return None
        return self.符號列[self._索引]

    def _取(self) -> 符號:
        符 = self._看()
        if 符 is None:
            self._拋出文法錯誤("意外之終", len(self.內容))
        self._索引 += 1
        return 符  # type: ignore[return-value]

    def _是關鍵詞(self, 符: 符號 | None, 詞: str) -> bool:
        return 符 is not None and 符.類别 == 詞 and 符.值 is None

    def _期(self, 詞: str) -> 符號:
        符 = self._取()
        if not self._是關鍵詞(符, 詞):
            self._拋出文法錯誤(f"當為「{詞}」", 符.位置.start)
        return 符

    def _期其一(self, 詞列: frozenset[str]) -> 符號:
        符 = self._取()
        if 符 is None or 符.值 is not None or 符.類别 not in 詞列:
            詞列文 = "、".join(sorted(詞列))
            self._拋出文法錯誤(
                f"當為其一「{詞列文}」", 符.位置.start if 符 else len(self.內容)
            )
        return 符

    def _拋出文法錯誤(self, 訊息: str, 索引: int) -> None:
        行號, 列偏移, 行文字 = 計算行列(self.內容, 索引)
        raise 文法之禍(訊息, (self.文檔名, 行號, 列偏移, 行文字))

    # ---- 值 -----------------------------------------------------------

    def _解析值(self) -> 值:
        符 = self._取()
        if self._是關鍵詞(符, "其"):
            return 其值(符.位置)
        if self._是關鍵詞(符, "其餘"):
            return 其餘值(符.位置)
        if self._是關鍵詞(符, "陰"):
            return 爻值(符.位置, False)
        if self._是關鍵詞(符, "陽"):
            return 爻值(符.位置, True)
        if 符.類别 == "名" and 符.值 is not None:
            return 名值(符.位置, 符.值)
        if 符.類别 == "言" and 符.值 is not None:
            return 言值(符.位置, 符.值)
        if 符.類别 == "數" and 符.值 is not None:
            return 數值(符.位置, 符.值)
        if 符.類别 == "數據" and 符.值 is not None:
            return 名值(符.位置, 符.值)
        self._拋出文法錯誤("不識之值", 符.位置.start)
        raise AssertionError("unreachable")

    def _解析名(self) -> str:
        符 = self._取()
        if 符.類别 != "名" or 符.值 is None:
            self._拋出文法錯誤("當為名", 符.位置.start)
        return 符.值

    def _解析數量(self) -> int:
        符 = self._取()
        if 符.類别 != "數" or 符.值 is None:
            self._拋出文法錯誤("當為數", 符.位置.start)
        if "." in 符.值:
            self._拋出文法錯誤("數量不可為小數", 符.位置.start)
        try:
            數量 = int(符.值)
        except ValueError:
            self._拋出文法錯誤("非法數量", 符.位置.start)
        if 數量 <= 0:
            self._拋出文法錯誤("數量不可為零", 符.位置.start)
        return 數量

    def _解析型別詞(self) -> str:
        符 = self._取()
        if 符.值 is not None or 符.類别 not in 內建型別詞:
            self._拋出文法錯誤("當為型別詞", 符.位置.start)
        return 符.類别

    # ---- 條件式 -------------------------------------------------------

    def _解析條件原子(self) -> 條件原子:
        值節 = self._解析值()
        下標: 值 | None = None
        之長 = False
        if self._是關鍵詞(self._看(), "之"):
            self._取()
            索 = self._解析值()
            下標 = 索
            位置 = slice(值節.位置.start, 索.位置.stop)
            return 條件原子(位置, 值節, 下標, 之長)
        if self._是關鍵詞(self._看(), "之長"):
            之長符 = self._取()
            之長 = True
            位置 = slice(值節.位置.start, 之長符.位置.stop)
            return 條件原子(位置, 值節, 下標, 之長)
        return 條件原子(值節.位置, 值節, 下標, 之長)

    def _解析條件式(self) -> list[條件原子 | str]:
        片段: list[條件原子 | str] = [self._解析條件原子()]
        while True:
            符 = self._看()
            if 符 is None:
                break
            if self._是關鍵詞(符, "者"):
                break
            if self._是關鍵詞(符, "或若") or self._是關鍵詞(符, "若非"):
                break
            if self._是關鍵詞(符, "云云") or self._是關鍵詞(符, "也"):
                break
            if 符.值 is None and 符.類别 in 比較詞對照:
                self._取()
                片段.append(比較詞對照[符.類别])
                片段.append(self._解析條件原子())
                continue
            if 符.值 is None and 符.類别 in 邏輯詞對照:
                self._取()
                片段.append(邏輯詞對照[符.類别])
                片段.append(self._解析條件原子())
                continue
            self._拋出文法錯誤("非法條件式", 符.位置.start)
        return 片段

    def _可視為區塊終止後繼(self, 符: 符號 | None) -> bool:
        if 符 is None:
            return False
        結構收束詞 = (
            "也",
            "云云",
            "若非",
            "或若",
            "是謂",
            "乃得",
            "乃得矣",
            "乃歸空無",
            "如事不諧",
            "豈",
            "不知何禍歟",
            "乃作罷",
        )
        if any(self._是關鍵詞(符, 詞) for 詞 in 結構收束詞):
            return False
        return True

    # ---- 語句 ---------------------------------------------------------

    def _解析語句列(self, 終止詞: frozenset[str]) -> list[句]:
        句列: list[句] = []
        while True:
            符 = self._看()
            if 符 is None:
                break
            if any(self._是關鍵詞(符, 詞) for 詞 in 終止詞):
                break
            句列.append(self._解析語句())
        return 句列

    def _解析語句(self) -> 句:
        符 = self._看()
        if 符 is None:
            self._拋出文法錯誤("意外之終", len(self.內容))

        if self._是關鍵詞(符, "吾嘗觀"):
            return self._解析匯入句()
        if self._是關鍵詞(符, "或云"):
            return self._解析宏句()
        if (
            self._是關鍵詞(符, "注曰")
            or self._是關鍵詞(符, "疏曰")
            or self._是關鍵詞(符, "批曰")
        ):
            return self._解析註釋句()
        if self._是關鍵詞(符, "姑妄行此"):
            return self._解析試句()
        if self._是關鍵詞(符, "嗚呼"):
            return self._解析擲句()
        if self._是關鍵詞(符, "取"):
            return self._解析取句()
        if self._是關鍵詞(符, "以施"):
            return self._解析以施句()
        if self._是關鍵詞(符, "施"):
            return self._解析施句()
        if self._是關鍵詞(符, "以"):
            下符 = (
                self.符號列[self._索引 + 1]
                if self._索引 + 1 < len(self.符號列)
                else None
            )
            if 下符 is not None and self._是關鍵詞(下符, "名之曰"):
                self._取()
                return self._解析命名句()
        if self._是關鍵詞(符, "充"):
            return self._解析列充句()
        if self._是關鍵詞(符, "銜"):
            return self._解析列銜句()
        if self._是關鍵詞(符, "其物如是"):
            return self._解析物定義句()
        if self._是關鍵詞(符, "凡"):
            return self._解析凡句()
        if self._是關鍵詞(符, "乃得矣"):
            return self._解析返回句(取棧=True)
        if self._是關鍵詞(符, "乃歸空無"):
            return self._解析返回句(空無=True)
        if self._是關鍵詞(符, "乃得"):
            return self._解析返回句()
        if self._是關鍵詞(符, "吾有") or self._是關鍵詞(符, "今有"):
            if self._是術定義起始():
                return self._解析術定義句()
            return self._解析宣告句()
        if self._是關鍵詞(符, "有"):
            return self._解析初始化句()
        if self._是關鍵詞(符, "名之曰"):
            return self._解析命名句()
        if self._是關鍵詞(符, "書之"):
            開 = self._取()
            return 書之句(開.位置)
        if self._是關鍵詞(符, "噫"):
            開 = self._取()
            return 噫句(開.位置)
        if self._是關鍵詞(符, "昔之"):
            return self._解析昔今句()
        if 符.值 is None and 符.類别 in {"加", "減", "乘", "除"}:
            return self._解析算術句()
        if self._是關鍵詞(符, "變"):
            開 = self._取()
            值節 = self._解析值()
            位置 = slice(開.位置.start, 值節.位置.stop)
            return 變句(位置, 值節)
        if self._是關鍵詞(符, "夫"):
            return self._解析夫句()
        if (
            self._是關鍵詞(符, "若")
            or self._是關鍵詞(符, "若其然者")
            or self._是關鍵詞(符, "若其不然者")
        ):
            return self._解析若句()
        if self._是關鍵詞(符, "恆為是"):
            return self._解析恆為是句()
        if self._是關鍵詞(符, "為是"):
            return self._解析為是遍句()
        if self._是關鍵詞(符, "是術曰") or self._是關鍵詞(符, "乃行是術曰"):
            self._拋出文法錯誤("術體不可獨立", 符.位置.start)
        if self._是關鍵詞(符, "乃止"):
            開 = self._取()
            return 乃止句(開.位置)
        if self._是關鍵詞(符, "乃止是遍"):
            開 = self._取()
            return 乃止是遍句(開.位置)
        if self._是關鍵詞(符, "也"):
            終 = self._取()
            return 註釋句(終.位置, "")
        if self._是關鍵詞(符, "云云"):
            self._拋出文法錯誤("不當之終", 符.位置.start)

        self._拋出文法錯誤("不識之句", 符.位置.start)
        raise AssertionError("unreachable")

    def _解析宣告句(self) -> 宣告句:
        開 = self._取()
        公開 = self._是關鍵詞(開, "今有")
        數量 = self._解析數量()
        類型 = self._解析型別詞()
        初值列: list[值] = []
        while self._是關鍵詞(self._看(), "曰"):
            self._取()
            初值列.append(self._解析值())
        名列: list[str] = []
        if self._是關鍵詞(self._看(), "名之曰"):
            self._取()
            名列.append(self._解析名())
            while self._是關鍵詞(self._看(), "曰"):
                self._取()
                名列.append(self._解析名())
        if len(初值列) > 數量:
            self._拋出文法錯誤("初值多於數量", 開.位置.start)
        if len(名列) > 數量:
            self._拋出文法錯誤("名多於數量", 開.位置.start)
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 宣告句(位置, 數量, 類型, 初值列, 名列, 公開)

    def _解析初始化句(self) -> 初始化句:
        開 = self._期("有")
        類型 = self._解析型別詞()
        初值 = self._解析值()
        名: str | None = None
        if self._是關鍵詞(self._看(), "名之曰"):
            self._取()
            名 = self._解析名()
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 初始化句(位置, 類型, 初值, 名)

    def _解析命名句(self) -> 命名句:
        開 = self._期("名之曰")
        名列 = [self._解析名()]
        while self._是關鍵詞(self._看(), "曰"):
            self._取()
            名列.append(self._解析名())
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 命名句(位置, 名列)

    def _是術定義起始(self) -> bool:
        起點 = self._索引
        if 起點 >= len(self.符號列):
            return False
        符 = self.符號列[起點]
        if not (self._是關鍵詞(符, "吾有") or self._是關鍵詞(符, "今有")):
            return False
        if 起點 + 2 >= len(self.符號列):
            return False
        if self.符號列[起點 + 1].類别 != "數":
            return False
        if not self._是關鍵詞(self.符號列[起點 + 2], "術"):
            return False
        探 = 起點 + 3
        止 = min(len(self.符號列), 探 + 64)
        while 探 < 止:
            符 = self.符號列[探]
            if self._是關鍵詞(符, "是術曰") or self._是關鍵詞(符, "乃行是術曰"):
                return True
            探 += 1
        return False

    def _解析術定義句(self) -> 術定義句:
        開 = self._取()
        公開 = self._是關鍵詞(開, "今有")
        數量 = self._解析數量()
        類型 = self._解析型別詞()
        if 類型 != "術":
            self._拋出文法錯誤("術定義須為術", 開.位置.start)
        if 數量 != 1:
            self._拋出文法錯誤("術定義數量須為一", 開.位置.start)
        if not self._是關鍵詞(self._看(), "名之曰"):
            self._拋出文法錯誤("術定義須命名", 開.位置.start)
        self._取()
        名 = self._解析名()
        if self._是關鍵詞(self._看(), "曰"):
            self._拋出文法錯誤("術名不可多", 開.位置.start)
        if self._是關鍵詞(self._看(), "欲行是術"):
            self._取()
        參數列: list[術參數] = []
        已見其餘參 = False
        if self._是關鍵詞(self._看(), "必先得"):
            self._取()
            while True:
                其餘參組 = self._是關鍵詞(self._看(), "其餘")
                if 其餘參組:
                    self._取()
                    組數量 = 1
                    組型別 = self._解析型別詞()
                else:
                    組數量 = self._解析數量()
                    組型別 = self._解析型別詞()
                名列: list[tuple[str, slice]] = []
                while self._是關鍵詞(self._看(), "曰"):
                    self._取()
                    名稱 = self._解析名()
                    名符 = self.符號列[self._索引 - 1]
                    名列.append((名稱, 名符.位置))
                if len(名列) != 組數量:
                    self._拋出文法錯誤(
                        "其餘參數須一名" if 其餘參組 else "參數數量不符",
                        開.位置.start,
                    )
                for 名稱, 位 in 名列:
                    參數列.append(術參數(位, 名稱, 組型別, 其餘參組))
                if 其餘參組:
                    已見其餘參 = True
                下符 = self._看()
                if 下符 is None:
                    break
                if 已見其餘參:
                    if 下符.類别 == "數" or self._是關鍵詞(下符, "其餘"):
                        self._拋出文法錯誤("其餘參數須居末", 下符.位置.start)
                    break
                if 下符.類别 == "數" or self._是關鍵詞(下符, "其餘"):
                    下二 = (
                        self.符號列[self._索引 + 1]
                        if self._索引 + 1 < len(self.符號列)
                        else None
                    )
                    if 下二 is not None and 下二.值 is None and 下二.類别 in 內建型別詞:
                        continue
                break
        if not (
            self._是關鍵詞(self._看(), "是術曰")
            or self._是關鍵詞(self._看(), "乃行是術曰")
        ):
            self._拋出文法錯誤("術體未始", 開.位置.start)
        self._取()
        體 = self._解析語句列(終止詞=frozenset({"是謂"}))
        self._期("是謂")
        self._解析名()
        終 = self._期("之術也")
        位置 = slice(開.位置.start, 終.位置.stop)
        return 術定義句(位置, 名, 參數列, 體, 公開)

    def _解析匯入句(self) -> 匯入句:
        開 = self._期("吾嘗觀")
        模組符 = self._取()
        if 模組符.類别 != "言" or 模組符.值 is None:
            self._拋出文法錯誤("當為書名", 模組符.位置.start)
        模組 = _還原言值(模組符.值)
        self._期("之書")
        名列: list[str] = []
        if self._是關鍵詞(self._看(), "方悟"):
            self._取()
            while True:
                符 = self._看()
                if 符 is None:
                    self._拋出文法錯誤("方悟未終", 開.位置.start)
                if self._是關鍵詞(符, "之義"):
                    self._取()
                    break
                名列.append(self._解析名())
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 匯入句(位置, 模組, 名列)

    def _解析宏句(self) -> 宏句:
        開 = self._期("或云")
        模式符 = self._取()
        if 模式符.類别 != "言" or 模式符.值 is None:
            self._拋出文法錯誤("宏式當為言", 模式符.位置.start)
        self._期("蓋謂")
        置換符 = self._取()
        if 置換符.類别 != "言" or 置換符.值 is None:
            self._拋出文法錯誤("宏替當為言", 置換符.位置.start)
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 宏句(位置, _還原言值(模式符.值), _還原言值(置換符.值))

    def _解析註釋句(self) -> 註釋句:
        開 = self._取()
        文符 = self._看()
        if 文符 is not None and 文符.類别 == "言" and 文符.值 is not None:
            self._取()
            位置 = slice(開.位置.start, 文符.位置.stop)
            return 註釋句(位置, _還原言值(文符.值))
        行終 = self.內容.find("\n", 開.位置.stop)
        if 行終 == -1:
            行終 = len(self.內容)
        文 = self.內容[開.位置.stop : 行終].strip()
        while True:
            觀 = self._看()
            if 觀 is None or 觀.位置.start >= 行終:
                break
            self._取()
        位置 = slice(開.位置.start, 行終)
        return 註釋句(位置, 文)

    def _解析試句(self) -> 試句:
        開 = self._期("姑妄行此")
        體 = self._解析語句列(終止詞=frozenset({"如事不諧"}))
        if not self._是關鍵詞(self._看(), "如事不諧"):
            self._拋出文法錯誤("試句未終", 開.位置.start)
        self._取()
        捕捉列: list[捕捉子句] = []
        while True:
            符 = self._看()
            if 符 is None:
                self._拋出文法錯誤("試句未終", 開.位置.start)
            if self._是關鍵詞(符, "乃作罷"):
                終 = self._取()
                位置 = slice(開.位置.start, 終.位置.stop)
                return 試句(位置, 體, 捕捉列)
            if self._是關鍵詞(符, "豈"):
                起 = 符.位置.start
                self._取()
                錯名 = self._解析值()
                self._期("之禍歟")
                變數名: str | None = None
                if self._是關鍵詞(self._看(), "名之曰"):
                    self._取()
                    變數名 = self._解析名()
                捕體 = self._解析語句列(
                    終止詞=frozenset({"豈", "不知何禍歟", "乃作罷"})
                )
                終符 = self.符號列[self._索引 - 1]
                捕捉列.append(
                    捕捉子句(slice(起, 終符.位置.stop), 錯名, 變數名, 捕體, False)
                )
                continue
            if self._是關鍵詞(符, "不知何禍歟"):
                起 = 符.位置.start
                self._取()
                變數名 = None
                if self._是關鍵詞(self._看(), "名之曰"):
                    self._取()
                    變數名 = self._解析名()
                捕體 = self._解析語句列(
                    終止詞=frozenset({"豈", "不知何禍歟", "乃作罷"})
                )
                終符 = self.符號列[self._索引 - 1]
                捕捉列.append(
                    捕捉子句(slice(起, 終符.位置.stop), None, 變數名, 捕體, True)
                )
                continue
            self._拋出文法錯誤("捕捉未始", 符.位置.start)

    def _解析擲句(self) -> 擲句:
        開 = self._期("嗚呼")
        名 = self._解析值()
        self._期("之禍")
        訊: 值 | None = None
        if self._是關鍵詞(self._看(), "曰"):
            self._取()
            訊 = self._解析值()
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 擲句(位置, 名, 訊)

    def _解析取句(self) -> 取句:
        開 = self._期("取")
        if self._是關鍵詞(self._看(), "其餘"):
            self._取()
            終 = self.符號列[self._索引 - 1]
            位置 = slice(開.位置.start, 終.位置.stop)
            return 取句(位置, None, True)
        數量 = self._解析數量()
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 取句(位置, 數量, False)

    def _解析以施句(self) -> 以施句:
        開 = self._期("以施")
        術 = self._解析值()
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 以施句(位置, 術)

    def _解析施句(self) -> 施句:
        開 = self._期("施")
        術 = self._解析值()
        參數列: list[值] = []
        while self._是關鍵詞(self._看(), "於"):
            self._取()
            參數列.append(self._解析值())
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 施句(位置, 術, 參數列)

    def _解析列充句(self) -> 列充句:
        開 = self._期("充")
        列 = self._解析值()
        值列: list[值] = []
        if not self._是關鍵詞(self._看(), "以"):
            self._拋出文法錯誤("充需以值", 開.位置.start)
        while self._是關鍵詞(self._看(), "以"):
            self._取()
            值列.append(self._解析值())
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 列充句(位置, 列, 值列)

    def _解析列銜句(self) -> 列銜句:
        開 = self._期("銜")
        列 = self._解析值()
        列列: list[值] = []
        if not self._是關鍵詞(self._看(), "以"):
            self._拋出文法錯誤("銜需以列", 開.位置.start)
        while self._是關鍵詞(self._看(), "以"):
            self._取()
            列列.append(self._解析值())
        終 = self.符號列[self._索引 - 1]
        位置 = slice(開.位置.start, 終.位置.stop)
        return 列銜句(位置, 列, 列列)

    def _解析物定義句(self) -> 物定義句:
        開 = self._期("其物如是")
        屬性列: list[物屬性] = []
        while self._是關鍵詞(self._看(), "物之"):
            self._取()
            鍵符 = self._取()
            if 鍵符.類别 != "言" or 鍵符.值 is None:
                self._拋出文法錯誤("物鍵當為言", 鍵符.位置.start)
            鍵 = 言值(鍵符.位置, 鍵符.值)
            self._期("者")
            類型 = self._解析型別詞()
            self._期("曰")
            值節 = self._解析值()
            終符 = self.符號列[self._索引 - 1]
            屬性列.append(
                物屬性(slice(鍵符.位置.start, 終符.位置.stop), 鍵, 類型, 值節)
            )
        self._期("是謂")
        名 = self._解析名()
        終 = self._期("之物也")
        位置 = slice(開.位置.start, 終.位置.stop)
        return 物定義句(位置, 名, 屬性列)

    def _解析凡句(self) -> 凡句:
        開 = self._期("凡")
        容器 = self._解析值()
        self._期("中之")
        變數名 = self._解析名()
        體 = self._解析語句列(終止詞=frozenset({"云云", "也"}))
        終符 = self._取()
        if not (self._是關鍵詞(終符, "云云") or self._是關鍵詞(終符, "也")):
            self._拋出文法錯誤("凡未終", 終符.位置.start)
        位置 = slice(開.位置.start, 終符.位置.stop)
        return 凡句(位置, 容器, 變數名, 體)

    def _解析返回句(self, 取棧: bool = False, 空無: bool = False) -> 返回句:
        開 = self._取()
        if 空無:
            位置 = slice(開.位置.start, 開.位置.stop)
            return 返回句(位置, None, False, True)
        if 取棧:
            位置 = slice(開.位置.start, 開.位置.stop)
            return 返回句(位置, None, True, False)
        值節 = self._解析值()
        終點 = 值節.位置.stop
        終符 = self._看()
        if 終符 is not None and (
            self._是關鍵詞(終符, "是矣") or self._是關鍵詞(終符, "是也")
        ):
            終點 = self._取().位置.stop
        位置 = slice(開.位置.start, 終點)
        return 返回句(位置, 值節, False, False)

    def _解析算術句(self) -> 算術句:
        開 = self._取()
        算 = 開.類别
        甲 = self._解析值()
        介 = self._取()
        if not (self._是關鍵詞(介, "以") or self._是關鍵詞(介, "於")):
            self._拋出文法錯誤("當為介詞", 介.位置.start)
        乙 = self._解析值()
        左, 右 = (甲, 乙) if self._是關鍵詞(介, "以") else (乙, 甲)
        if 算 == "加":
            運 = "+"
        elif 算 == "減":
            運 = "-"
        elif 算 == "乘":
            運 = "*"
        else:
            運 = "/"
        if 算 == "除" and self._是關鍵詞(self._看(), "所餘幾何"):
            mod符 = self._取()
            運 = "%"
            終點 = mod符.位置.stop
        else:
            終點 = 乙.位置.stop
        位置 = slice(開.位置.start, 終點)
        return 算術句(位置, 運, 左, 右)

    def _解析夫句(self) -> 句:
        開 = self._期("夫")
        甲 = self._解析值()
        if self._是關鍵詞(self._看(), "之"):
            self._取()
            索 = self._解析值()
            位置 = slice(開.位置.start, 索.位置.stop)
            節點: 句 = 之句(位置, 甲, 索)
            if self._是關鍵詞(self._看(), "者"):
                self._取()
            return 節點
        if self._是關鍵詞(self._看(), "之長"):
            之長符 = self._取()
            位置 = slice(開.位置.start, 之長符.位置.stop)
            節點 = 之長句(位置, 甲)
            if self._是關鍵詞(self._看(), "者"):
                self._取()
            return 節點
        # 邏輯二元：夫 <甲> <乙> 中有陽乎/中無陰乎
        符 = self._看()
        若可值 = 符 is not None and (
            (符.類别 in {"名", "言", "數", "數據"} and 符.值 is not None)
            or self._是關鍵詞(符, "其")
            or self._是關鍵詞(符, "陰")
            or self._是關鍵詞(符, "陽")
        )
        if 若可值:
            乙 = self._解析值()
            op符 = self._看()
            if op符 is not None and op符.值 is None and op符.類别 in 邏輯詞對照:
                self._取()
                運 = 邏輯詞對照[op符.類别]
                位置 = slice(開.位置.start, op符.位置.stop)
                節點 = 算術句(位置, 運, 甲, 乙)
                if self._是關鍵詞(self._看(), "者"):
                    self._取()
                return 節點
            # 回退：非邏輯二元，視為僅取值
            self._索引 -= 1
        位置 = slice(開.位置.start, 甲.位置.stop)
        節點 = 夫句(位置, 甲)
        if self._是關鍵詞(self._看(), "者"):
            self._取()
        return 節點

    def _解析昔今句(self) -> 昔今句:
        開 = self._期("昔之")
        左名 = self._解析名()
        左下標: 值 | None = None
        if self._是關鍵詞(self._看(), "之"):
            self._取()
            左下標 = self._解析值()
        self._期("者")
        self._期("今")
        if self._是關鍵詞(self._看(), "不復存矣"):
            終 = self._取()
            終點 = 終.位置.stop
            if self._是關鍵詞(self._看(), "是也"):
                是也符 = self._取()
                終點 = 是也符.位置.stop
                # 與 @wenyan/cli 對齊：刪除後可寫「是也」，且僅在可收束區塊時保留「也」作終止。
                if self._可視為區塊終止後繼(self._看()):
                    self.符號列.insert(self._索引, 符號("也", None, 是也符.位置))
            位置 = slice(開.位置.start, 終點)
            return 昔今句(位置, 左名, 左下標, None, None, True)
        右值 = self._解析值()
        右下標: 值 | None = None
        if self._是關鍵詞(self._看(), "之"):
            self._取()
            右下標 = self._解析值()
        終符 = self._看()
        if 終符 is not None and self._是關鍵詞(終符, "是矣"):
            終 = self._取()
            位置 = slice(開.位置.start, 終.位置.stop)
            return 昔今句(位置, 左名, 左下標, 右值, 右下標, False)
        if 終符 is not None and self._是關鍵詞(終符, "是也"):
            終 = self._取()
            if self._可視為區塊終止後繼(self._看()):
                # 與 @wenyan/cli 對齊："是也" 視情境可等價於 "是" + "也"，保留 "也" 作區塊終止。
                self.符號列.insert(self._索引, 符號("也", None, 終.位置))
            位置 = slice(開.位置.start, 終.位置.stop)
            return 昔今句(位置, 左名, 左下標, 右值, 右下標, False)
        if 終符 is not None and 終符.類别 == "數據" and 終符.值 == "是":
            終 = self._取()
            終點 = 終.位置.stop
            下符 = self._看()
            if self._是關鍵詞(下符, "也") and 下符 is not None:
                夾段 = self.內容[終.位置.stop : 下符.位置.start]
                if not any(字 in "。、，" for 字 in 夾段):
                    終點 = self._取().位置.stop
            位置 = slice(開.位置.start, 終點)
            return 昔今句(位置, 左名, 左下標, 右值, 右下標, False)
        if 終符 is not None and self._是關鍵詞(終符, "也"):
            終 = self._取()
            位置 = slice(開.位置.start, 終.位置.stop)
            return 昔今句(位置, 左名, 左下標, 右值, 右下標, False)
        位置 = slice(開.位置.start, self.符號列[self._索引 - 1].位置.stop)
        return 昔今句(位置, 左名, 左下標, 右值, 右下標, False)

    def _解析若句(self) -> 若句:
        開 = self._取()
        反轉 = False
        if self._是關鍵詞(開, "若其然者"):
            條件: list[條件原子 | str] = [條件原子(開.位置, 其值(開.位置), None, False)]
        elif self._是關鍵詞(開, "若其不然者"):
            反轉 = True
            條件 = [條件原子(開.位置, 其值(開.位置), None, False)]
        else:
            條件 = self._解析條件式()
            self._期("者")
        然 = self._解析語句列(終止詞=frozenset({"或若", "若非", "云云", "也", "是謂"}))
        另若列: list[或若子句] = []
        while self._是關鍵詞(self._看(), "或若"):
            或若開 = self._取()
            或若條 = self._解析條件式()
            self._期("者")
            或若體 = self._解析語句列(
                終止詞=frozenset({"或若", "若非", "云云", "也", "是謂"})
            )
            終 = self.符號列[self._索引 - 1]
            另若列.append(
                或若子句(slice(或若開.位置.start, 終.位置.stop), 或若條, 或若體)
            )
        否則: list[句] = []
        if self._是關鍵詞(self._看(), "若非"):
            self._取()
            否則 = self._解析語句列(終止詞=frozenset({"云云", "也", "是謂"}))
        終結 = self._看()
        if 終結 is None:
            終點 = 開.位置.stop
            if 否則:
                終點 = 否則[-1].位置.stop
            elif 另若列:
                終點 = 另若列[-1].位置.stop
            elif 然:
                終點 = 然[-1].位置.stop
            位置 = slice(開.位置.start, 終點)
            return 若句(位置, 條件, 反轉, 然, 另若列, 否則)
        if self._是關鍵詞(終結, "云云") or self._是關鍵詞(終結, "也"):
            終符 = self._取()
            位置 = slice(開.位置.start, 終符.位置.stop)
            return 若句(位置, 條件, 反轉, 然, 另若列, 否則)
        if self._是關鍵詞(終結, "是謂"):
            終點 = 開.位置.stop
            if 否則:
                終點 = 否則[-1].位置.stop
            elif 另若列:
                終點 = 另若列[-1].位置.stop
            elif 然:
                終點 = 然[-1].位置.stop
            位置 = slice(開.位置.start, 終點)
            return 若句(位置, 條件, 反轉, 然, 另若列, 否則)
        self._拋出文法錯誤("若未終", 開.位置.start)

    def _解析恆為是句(self) -> 恆為是句:
        開 = self._期("恆為是")
        體 = self._解析語句列(
            終止詞=frozenset({"云云", "也", "是謂", "乃得", "乃得矣", "乃歸空無"})
        )
        終符 = self._看()
        if 終符 is not None and (
            self._是關鍵詞(終符, "云云") or self._是關鍵詞(終符, "也")
        ):
            終取 = self._取()
            位置 = slice(開.位置.start, 終取.位置.stop)
            return 恆為是句(位置, 體)
        if 終符 is not None and self._是關鍵詞(終符, "是謂"):
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 恆為是句(位置, 體)
        if 終符 is not None and (
            self._是關鍵詞(終符, "乃得")
            or self._是關鍵詞(終符, "乃得矣")
            or self._是關鍵詞(終符, "乃歸空無")
        ):
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 恆為是句(位置, 體)
        if 終符 is None:
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 恆為是句(位置, 體)
        self._拋出文法錯誤("循環未終", 終符.位置.start)

    def _解析為是遍句(self) -> 為是遍句:
        開 = self._期("為是")
        次數 = self._解析值()
        self._期("遍")
        體 = self._解析語句列(
            終止詞=frozenset({"云云", "也", "是謂", "乃得", "乃得矣", "乃歸空無"})
        )
        終符 = self._看()
        if 終符 is not None and (
            self._是關鍵詞(終符, "云云") or self._是關鍵詞(終符, "也")
        ):
            終取 = self._取()
            位置 = slice(開.位置.start, 終取.位置.stop)
            return 為是遍句(位置, 次數, 體)
        if 終符 is not None and self._是關鍵詞(終符, "是謂"):
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 為是遍句(位置, 次數, 體)
        if 終符 is not None and (
            self._是關鍵詞(終符, "乃得")
            or self._是關鍵詞(終符, "乃得矣")
            or self._是關鍵詞(終符, "乃歸空無")
        ):
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 為是遍句(位置, 次數, 體)
        if 終符 is None:
            終點 = 體[-1].位置.stop if 體 else 開.位置.stop
            位置 = slice(開.位置.start, 終點)
            return 為是遍句(位置, 次數, 體)
        self._拋出文法錯誤("循環未終", 終符.位置.start)


def _前處理錯誤(內容: str, 文檔名: str, 訊息: str, 索引: int) -> None:
    行號, 列偏移, 行文字 = 計算行列(內容, 索引)
    raise 文法之禍(訊息, (文檔名, 行號, 列偏移, 行文字))


def _建立編譯環境() -> 編譯環境:
    根目錄 = os.path.dirname(os.path.abspath(__file__))
    return 編譯環境(根目錄, {}, {}, {}, set(), set(), set())


def _取得當前目錄(文檔名: str) -> str:
    if 文檔名 in {"<言>", "<stdin>"}:
        return os.getcwd()
    路徑 = 文檔名
    if not os.path.isabs(路徑):
        路徑 = os.path.abspath(路徑)
    return os.path.dirname(路徑)


def _解析模組路徑(
    模組: str, 文檔名: str, 內容: str, 位置: slice, 環境: 編譯環境
) -> str:
    相對 = 模組.replace("/", os.sep)
    當前目錄 = _取得當前目錄(文檔名)
    根庫目錄 = os.path.join(環境.根目錄, "lib")
    平台庫目錄 = os.path.join(環境.根目錄, "lib", "py")
    if 相對 == "曆法":
        搜尋目錄 = [當前目錄, 根庫目錄, 平台庫目錄]
    else:
        搜尋目錄 = [當前目錄, 平台庫目錄, 根庫目錄]
    for 基 in 搜尋目錄:
        候選 = os.path.join(基, f"{相對}.wy")
        if os.path.isfile(候選):
            return os.path.abspath(候選)
        候選 = os.path.join(基, 相對, "序.wy")
        if os.path.isfile(候選):
            return os.path.abspath(候選)
    _前處理錯誤(內容, 文檔名, "匯入之書不見", 位置.start)
    raise AssertionError("unreachable")


def _讀取源碼(路徑: str, 環境: 編譯環境) -> str:
    if 路徑 in 環境.源碼快取:
        return 環境.源碼快取[路徑]
    with open(路徑, "r", encoding="utf-8") as 檔案:
        內容 = 檔案.read()
    環境.源碼快取[路徑] = 內容
    return 內容


內建序言源碼 = '''
import json

__暫存 = []
__文言負索 = {}


def __其():
    if not __暫存:
        return None
    __其值 = __暫存[-1]
    __暫存.clear()
    return __其值


def __取(數量):
    if 數量 <= 0:
        return []
    if 數量 > len(__暫存):
        raise 文言之禍("虛指", "取值不足")
    片 = __暫存[-數量:]
    del __暫存[-數量:]
    return 片


def __取其餘():
    if not __暫存:
        return []
    片 = __暫存[:]
    __暫存.clear()
    return 片


def __文言呼叫(術, *args):
    try:
        需 = 術.__文言術參數數__
    except AttributeError:
        return 術(*args)
    接其餘 = getattr(術, "__文言術接其餘__", False)
    已 = len(args)
    if 已 >= 需:
        if 接其餘:
            return 術(*args)
        結 = 術(*args[:需])
        if 已 == 需:
            return 結
        return __文言呼叫(結, *args[需:])

    def _後續(*後):
        return __文言呼叫(術, *(args + 後))

    _後續.__文言術參數數__ = 需 - 已
    _後續.__文言術接其餘__ = 接其餘
    return _後續


def 取物(物, 端):
    if isinstance(端, str):
        if isinstance(物, dict):
            return 物.get(端)
        try:
            return 物[端]
        except Exception:
            return None

    索 = int(端)
    if isinstance(物, list):
        if 索 <= 0:
            return __文言負索.get((id(物), 索))
        if 索 > len(物):
            return None
        return 物[索 - 1]

    try:
        return 物[索 - 1]
    except Exception:
        return None


def 置物(物, 端, 實):
    if isinstance(端, str):
        try:
            物[端] = 實
        except Exception:
            return 實
        return 實

    索 = int(端)
    if isinstance(物, list):
        if 索 <= 0:
            __文言負索[(id(物), 索)] = 實
            return 實
        索 -= 1
        if 索 >= len(物):
            物.extend([None] * (索 - len(物) + 1))
        物[索] = 實
        return 實

    物[索 - 1] = 實
    return 實


def 刪物(物, 端):
    if isinstance(端, str):
        if isinstance(物, dict):
            物.pop(端, None)
            return None
        try:
            del 物[端]
        except Exception:
            return None
        return None

    索 = int(端)
    if isinstance(物, list):
        if 索 <= 0:
            __文言負索.pop((id(物), 索), None)
            return None
        if 索 <= len(物):
            del 物[索 - 1]
        return None

    try:
        del 物[索 - 1]
    except Exception:
        return None
    return None


def 列物之端(物):
    if isinstance(物, dict):
        return list(物.keys())
    try:
        return list(物)
    except Exception:
        return []


def 識類(元):
    if isinstance(元, list):
        return "列"
    if isinstance(元, bool):
        return "爻"
    if isinstance(元, (int, float)):
        return "數"
    if isinstance(元, str):
        return "言"
    if callable(元):
        return "術"
    if isinstance(元, dict):
        return "物"
    return "元"


def 文言轉整(值, 預設=0):
    try:
        return int(float(值))
    except (TypeError, ValueError):
        return int(預設)


class 文言之禍(Exception):
    def __init__(self, 名, 訊=None):
        super().__init__(訊)
        self.名 = 名
        self.訊 = 訊

    def __getitem__(self, 鍵):
        if 鍵 == "名":
            return self.名
        if 鍵 == "訊":
            return self.訊
        return None


class JSON:
    @staticmethod
    def _正規(物):
        if isinstance(物, float) and 物.is_integer():
            return int(物)
        if isinstance(物, list):
            return [JSON._正規(元) for 元 in 物]
        if isinstance(物, dict):
            return {鍵: JSON._正規(值) for 鍵, 值 in 物.items()}
        return 物

    @staticmethod
    def stringify(物):
        try:
            return json.dumps(JSON._正規(物), ensure_ascii=False, separators=(",", ":"))
        except TypeError:
            return str(物)


class String:
    @staticmethod
    def fromCharCode(值):
        try:
            return chr(int(值))
        except (TypeError, ValueError):
            return ""


def __文言餘項文字(餘項):
    if 餘項 == 1:
        return "... 1 more item"
    return f"... {餘項} more items"


def __文言可單行(項列, 起算, 斷行寬):
    總長 = len(項列) + 起算
    if 總長 + len(項列) > 斷行寬:
        return False
    for 項 in 項列:
        總長 += len(項)
        if 總長 > 斷行寬:
            return False
    return True


def __文言分組列元素(項列, 原列, 縮排, 斷行寬, 緊湊度, 列上限):
    總長 = 0
    最長 = 0
    可分組項數 = len(項列)
    if len(原列) > 列上限 and 項列:
        # 最後的「... n more items」不參與欄位計算。
        可分組項數 -= 1

    資料長 = [0] * 可分組項數
    for 索 in range(可分組項數):
        長度 = len(項列[索])
        資料長[索] = 長度
        總長 += 長度 + 2
        if 長度 > 最長:
            最長 = 長度

    欄寬 = 最長 + 2
    if not (
        欄寬 * 3 + 縮排 < 斷行寬
        and (總長 / 欄寬 > 5 or 最長 <= 6)
    ):
        return 項列

    偏置 = max(欄寬 - 總長 / len(項列), 0.0) ** 0.5
    估欄寬 = max(欄寬 - 3 - 偏置, 1)
    欄數 = min(
        round((2.5 * 估欄寬 * 可分組項數) ** 0.5 / 估欄寬),
        (斷行寬 - 縮排) // max(欄寬, 1),
        緊湊度 * 4,
        15,
    )
    if 欄數 <= 1:
        return 項列

    各欄寬: list[int] = []
    for 欄 in range(欄數):
        行最長 = 0
        for 索 in range(欄, 可分組項數, 欄數):
            if 資料長[索] > 行最長:
                行最長 = 資料長[索]
        各欄寬.append(行最長 + 2)

    左補齊 = True
    for 值 in 原列[:可分組項數]:
        if isinstance(值, bool) or not isinstance(值, (int, float)):
            左補齊 = False
            break

    分組: list[str] = []
    for 首 in range(0, 可分組項數, 欄數):
        末 = min(首 + 欄數, 可分組項數)
        行片: list[str] = []
        for 索 in range(首, 末 - 1):
            欄位文 = f"{項列[索]}, "
            欄寬度 = 各欄寬[索 - 首]
            行片.append(欄位文.rjust(欄寬度) if 左補齊 else 欄位文.ljust(欄寬度))

        尾索 = 末 - 1
        if 左補齊:
            行片.append(項列[尾索].rjust(max(各欄寬[尾索 - 首] - 2, 0)))
        else:
            行片.append(項列[尾索])
        分組.append("".join(行片))

    if len(原列) > 列上限:
        分組.append(項列[可分組項數])
    return 分組


def __文言格式列(列值, 縮排):
    斷行寬 = 80
    緊湊度 = 3
    列上限 = 100

    項列 = [__文言格式輸出值(元, 縮排 + 2) for 元 in 列值[:列上限]]
    if len(列值) > 列上限:
        項列.append(__文言餘項文字(len(列值) - 列上限))

    原長 = len(項列)
    if 項列 and 緊湊度 >= 1 and len(項列) > 6:
        項列 = __文言分組列元素(項列, 列值, 縮排, 斷行寬, 緊湊度, 列上限)

    if 原長 == len(項列):
        起算 = len(項列) + 縮排 + 1 + 10
        if __文言可單行(項列, 起算, 斷行寬):
            併 = ", ".join(項列)
            if "\\n" not in 併:
                return f"[ {併} ]"

    前綴 = "\\n" + (" " * 縮排)
    return "[" + 前綴 + "  " + ("," + 前綴 + "  ").join(項列) + 前綴 + "]"


def __文言格式輸出值(值, 縮排=0):
    if isinstance(值, bool):
        return "true" if 值 else "false"
    if isinstance(值, float):
        if 值.is_integer():
            return str(int(值))
        return str(值)
    if isinstance(值, int):
        return str(值)
    if isinstance(值, list):
        return __文言格式列(值, 縮排)
    if 值 is None:
        return "None"
    return str(值)


def __文言輸出列(值列):
    if not globals().get("__wenyan_no_output_hanzi__", False):
        return 值列
    return [__文言格式輸出值(值, 0) for 值 in 值列]


JSON.stringify.__文言術參數數__ = 1
String.fromCharCode.__文言術參數數__ = 1
取物.__文言術參數數__ = 2
置物.__文言術參數數__ = 3
刪物.__文言術參數數__ = 2
列物之端.__文言術參數數__ = 1
識類.__文言術參數數__ = 1
'''


def _內建序言AST() -> list[ast.stmt]:
    return ast.parse(內建序言源碼, filename="<內建序言>").body


def _掃描匯入(內容: str, 文檔名: str) -> list[tuple[str, slice]]:
    符列 = list(詞法分析器(內容, 文檔名))
    結果: list[tuple[str, slice]] = []
    索引 = 0
    while 索引 < len(符列):
        符 = 符列[索引]
        if 符.值 is None and 符.類别 == "吾嘗觀":
            if 索引 + 1 < len(符列):
                書符 = 符列[索引 + 1]
                if 書符.類别 == "言" and 書符.值 is not None:
                    結果.append((_還原言值(書符.值), 符.位置))
                    索引 += 2
                    continue
        索引 += 1
    return 結果


def _編譯宏(模式: str, 置換: str) -> 宏定義:
    佔位符 = "甲乙丙丁戊己庚辛壬癸"
    片段: list[str] = []
    佔位列: list[str] = []
    索引 = 0
    while 索引 < len(模式):
        if (
            模式[索引] == "「"
            and 索引 + 2 < len(模式)
            and 模式[索引 + 2] == "」"
            and 模式[索引 + 1] in 佔位符
        ):
            片段.append("(.+?)")
            佔位列.append(模式[索引 + 1])
            索引 += 3
            continue
        片段.append(re.escape(模式[索引]))
        索引 += 1
    正則 = re.compile("".join(片段))
    return 宏定義(模式, 置換, 正則, 佔位列)


def 收集宏(內容: str, 文檔名: str) -> list[宏定義]:
    符列 = list(詞法分析器(內容, 文檔名))
    結果: list[宏定義] = []
    索引 = 0
    while 索引 < len(符列):
        符 = 符列[索引]
        if 符.值 is None and 符.類别 == "或云":
            if 索引 + 3 < len(符列):
                模式符 = 符列[索引 + 1]
                謂符 = 符列[索引 + 2]
                置換符 = 符列[索引 + 3]
                if (
                    模式符.類别 == "言"
                    and 模式符.值 is not None
                    and 謂符.值 is None
                    and 謂符.類别 == "蓋謂"
                    and 置換符.類别 == "言"
                    and 置換符.值 is not None
                ):
                    模式 = _還原言值(模式符.值)
                    置換 = _還原言值(置換符.值)
                    結果.append(_編譯宏(模式, 置換))
                    索引 += 4
                    continue
        索引 += 1
    return 結果


def _替換宏(宏: 宏定義, 匹配: re.Match) -> str:
    置換 = 宏.置換
    if not 宏.占位列:
        return 置換
    佔位符 = "甲乙丙丁戊己庚辛壬癸"
    片段: list[str] = []
    索引 = 0
    while 索引 < len(置換):
        if (
            置換[索引] == "「"
            and 索引 + 2 < len(置換)
            and 置換[索引 + 2] == "」"
            and 置換[索引 + 1] in 佔位符
        ):
            佔位 = 置換[索引 + 1]
            if 佔位 in 宏.占位列:
                序 = 宏.占位列.index(佔位)
                片段.append(匹配.group(序 + 1))
            else:
                片段.append("「" + 佔位 + "」")
            索引 += 3
            continue
        片段.append(置換[索引])
        索引 += 1
    return "".join(片段)


def _跳過引號(內容: str, 起點: int, 文檔名: str) -> int:
    if 內容.startswith("「「", 起點):
        索引 = 起點 + 2
        層級 = 2
    elif 內容.startswith("『", 起點):
        索引 = 起點 + 1
        層級 = 2
    elif 內容.startswith("「", 起點):
        索引 = 內容.find("」", 起點 + 1)
        if 索引 == -1:
            _前處理錯誤(內容, 文檔名, "名未尽", 起點)
        return 索引 + 1
    else:
        return 起點 + 1
    while 索引 < len(內容):
        字 = 內容[索引]
        if 字 == "「":
            層級 += 1
            索引 += 1
            continue
        if 字 == "」":
            層級 -= 1
            索引 += 1
            if 層級 == 0:
                return 索引
            continue
        if 字 == "『":
            層級 += 2
            索引 += 1
            continue
        if 字 == "』":
            層級 -= 2
            索引 += 1
            if 層級 == 0:
                return 索引
            continue
        索引 += 1
    _前處理錯誤(內容, 文檔名, "言未尽", 起點)
    raise AssertionError("unreachable")


def 擴展宏(內容: str, 宏列: list[宏定義], 文檔名: str) -> str:
    if not 宏列:
        return 內容
    for 宏 in 宏列:
        起始 = 0
        while True:
            字串範圍: list[tuple[int, int]] = []
            索引 = 0
            while 索引 < len(內容):
                if 內容.startswith("「「", 索引) or 內容.startswith("『", 索引):
                    終 = _跳過引號(內容, 索引, 文檔名)
                    字串範圍.append((索引, 終))
                    索引 = 終
                    continue
                索引 += 1

            匹配 = 宏.正則.search(內容, 起始)
            if 匹配 is None:
                break
            起點 = 匹配.start()
            範圍終: int | None = None
            for 左, 右 in 字串範圍:
                if 左 <= 起點 < 右:
                    範圍終 = 右
                    break
            if 範圍終 is not None:
                起始 = 範圍終
                continue
            替換 = _替換宏(宏, 匹配)
            內容 = 內容[: 匹配.start()] + 替換 + 內容[匹配.end() :]
            起始 = 匹配.start()
    return 內容


def _收集宏遞迴(
    路徑: str, 文檔名: str, 內容: str, 位置: slice, 環境: 編譯環境
) -> list[宏定義]:
    if 路徑 in 環境.宏快取:
        return 環境.宏快取[路徑]
    if 路徑 in 環境.宏解析中:
        _前處理錯誤(內容, 文檔名, "循環匯入", 位置.start)
    環境.宏解析中.add(路徑)
    原文 = _讀取源碼(路徑, 環境)
    匯入列 = _掃描匯入(原文, 路徑)
    宏列: list[宏定義] = []
    for 模組, 位 in 匯入列:
        模組路徑 = _解析模組路徑(模組, 路徑, 原文, 位, 環境)
        宏列.extend(_收集宏遞迴(模組路徑, 路徑, 原文, 位, 環境))
    宏列.extend(收集宏(原文, 路徑))
    環境.宏解析中.remove(路徑)
    環境.宏快取[路徑] = 宏列
    return 宏列


def _前處理源碼(內容: str, 文檔名: str, 環境: 編譯環境) -> str:
    匯入列 = _掃描匯入(內容, 文檔名)
    宏列: list[宏定義] = []
    for 模組, 位 in 匯入列:
        模組路徑 = _解析模組路徑(模組, 文檔名, 內容, 位, 環境)
        宏列.extend(_收集宏遞迴(模組路徑, 文檔名, 內容, 位, 環境))
    宏列.extend(收集宏(內容, 文檔名))
    return 擴展宏(內容, 宏列, 文檔名)


def _解析前處理(內容: str, 文檔名: str, 環境: 編譯環境) -> tuple[程式, str]:
    處理後 = _前處理源碼(內容, 文檔名, 環境)
    程 = 文法分析器(處理後, 文檔名).解析程式()
    return 程, 處理後


def 解析(內容: str, 文檔名: str = "<言>") -> 程式:
    """文言源碼轉 Wenyan AST。"""

    環境 = _建立編譯環境()
    程, _ = _解析前處理(內容, 文檔名, 環境)
    return 程


def _還原言值(文: str) -> str:
    """將 lexer 的最小轉義字串還原成真實字元。"""

    return 文.replace("\\n", "\n").replace('\\"', '"')


def _造索引(值: ast.expr) -> ast.slice:
    """建立 `ast.Subscript` 所需的 slice/index 相容表示。"""

    if hasattr(ast, "Index"):
        return ast.Index(value=值)  # type: ignore[attr-defined, return-value]
    return 值  # type: ignore[return-value]


@dataclass
class 作用域資訊:
    """函數作用域所需宣告。"""

    全域: set[str]
    非區: set[str]


@dataclass
class _作用域節點:
    父: _作用域節點 | None
    本地: set[str]
    賦值: set[str]
    子: list[_作用域節點]
    術節: 術定義句 | None


def _分析作用域(句列: list[句]) -> dict[int, 作用域資訊]:
    根 = _作用域節點(None, set(), set(), [], None)

    def 收集(列: list[句], 節點: _作用域節點) -> None:
        for 節 in 列:
            if isinstance(節, 宣告句):
                節點.本地.update(節.名列)
            elif isinstance(節, 初始化句):
                if 節.名 is not None:
                    節點.本地.add(節.名)
            elif isinstance(節, 命名句):
                節點.本地.update(節.名列)
            elif isinstance(節, 物定義句):
                節點.本地.add(節.名)
            elif isinstance(節, 凡句):
                節點.本地.add(節.變數名)
                收集(節.體, 節點)
            elif isinstance(節, 試句):
                收集(節.體, 節點)
                for 捕 in 節.捕捉列:
                    if 捕.變數名 is not None:
                        節點.本地.add(捕.變數名)
                    收集(捕.體, 節點)
            elif isinstance(節, 若句):
                收集(節.然, 節點)
                收集(節.否則, 節點)
                for 或若 in 節.另若列:
                    收集(或若.體, 節點)
            elif isinstance(節, 恆為是句):
                收集(節.體, 節點)
            elif isinstance(節, 為是遍句):
                收集(節.體, 節點)
            elif isinstance(節, 術定義句):
                節點.本地.add(節.名)
                子節 = _作用域節點(節點, set(), set(), [], 節)
                子節.本地.update([參.名 for 參 in 節.參數列])
                節點.子.append(子節)
                收集(節.體, 子節)
            elif isinstance(節, 昔今句):
                if 節.左下標 is None:
                    節點.賦值.add(節.左名)

    def 計算(節點: _作用域節點, 結果: dict[int, 作用域資訊]) -> None:
        for 子 in 節點.子:
            全域: set[str] = set()
            非區: set[str] = set()
            for 名 in 子.賦值:
                if 名 in 子.本地:
                    continue
                父 = 子.父
                while 父 is not None:
                    if 名 in 父.本地:
                        if 父.術節 is None:
                            全域.add(名)
                        else:
                            非區.add(名)
                        break
                    父 = 父.父
                else:
                    全域.add(名)
            if 子.術節 is not None:
                結果[id(子.術節)] = 作用域資訊(全域, 非區)
            計算(子, 結果)

    收集(句列, 根)
    結果: dict[int, 作用域資訊] = {}
    計算(根, 結果)
    return 結果


class PythonAST轉譯器:
    """將 Wenyan AST 轉譯為 Python `ast`。"""

    def __init__(
        self,
        內容: str,
        文檔名: str = "<言>",
        環境: 編譯環境 | None = None,
        插入序言: bool = True,
    ) -> None:
        self.內容 = 內容
        self.文檔名 = 文檔名
        self._內部序 = 0
        檔鑰 = 文檔名 if os.path.isabs(文檔名) else os.path.abspath(文檔名)
        self._內部前綴 = f"{abs(hash(檔鑰)) & 0xFFFF:x}"
        self._暫存名 = "__暫存"
        self._其函名 = "__其"
        self._待取數: int | None = None
        self._待取其餘 = False
        self._作用域資訊: dict[int, 作用域資訊] = {}
        self._環境 = 環境 if 環境 is not None else _建立編譯環境()
        self._插入序言 = 插入序言

    def 轉譯(self, 程: 程式) -> ast.Module:
        """轉譯整個程式。"""

        主體: list[ast.stmt] = []
        if self._插入序言:
            主體.extend(self._序言())
        主體.extend(self._轉譯句列(程))
        模組 = ast.Module(body=主體, type_ignores=[])
        return ast.fix_missing_locations(模組)

    def _序言(self) -> list[ast.stmt]:
        return _內建序言AST()

    def _轉譯句列(self, 程: 程式) -> list[ast.stmt]:
        self._待取數 = None
        self._待取其餘 = False
        self._作用域資訊 = _分析作用域(程.句列)
        return self._轉句列(程.句列)

    def _新內部名(self, 前綴: str) -> str:
        self._內部序 += 1
        名 = f"__{前綴}{self._內部前綴}_{self._內部序}"
        return 名 if 名.isidentifier() else f"__tmp{self._內部前綴}_{self._內部序}"

    def _拋出文法錯誤(self, 訊息: str, 索引: int) -> None:
        行號, 列偏移, 行文字 = 計算行列(self.內容, 索引)
        raise 文法之禍(訊息, (self.文檔名, 行號, 列偏移, 行文字))

    def _檢名(self, 名: str, 位置: slice) -> None:
        if not 名.isidentifier() or keyword.iskeyword(名):
            self._拋出文法錯誤("名不合 Python 識別字", 位置.start)

    def _轉JS片段(self, 文: str) -> ast.expr | None:
        簡 = "".join(文.split())
        if 簡 == '(()=>document.getElementById("out").innerHTML="")':
            return ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=ast.Constant(value=None),
            )
        if re.fullmatch(r"\(x=>setInterval\(x,\d+\)\)", 簡):
            return ast.Lambda(
                args=ast.arguments(
                    posonlyargs=[],
                    args=[ast.arg(arg="x", annotation=None)],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=ast.Call(func=ast.Name(id="x", ctx=ast.Load()), args=[], keywords=[]),
            )
        return None

    def _轉值(self, 節: 值) -> ast.expr:
        if isinstance(節, 名值):
            if 節.名.isidentifier() and not keyword.iskeyword(節.名):
                return ast.Name(id=節.名, ctx=ast.Load())
            JS代 = self._轉JS片段(節.名)
            if JS代 is not None:
                return JS代
            try:
                return ast.parse(節.名, mode="eval").body
            except SyntaxError:
                self._拋出文法錯誤("名不合 Python 表達式", 節.位置.start)
        if isinstance(節, 言值):
            return ast.Constant(value=_還原言值(節.文))
        if isinstance(節, 數值):
            try:
                if "." in 節.文:
                    return ast.Constant(value=float(節.文))
                return ast.Constant(value=int(節.文))
            except ValueError:
                self._拋出文法錯誤("非法數值", 節.位置.start)
        if isinstance(節, 爻值):
            return ast.Constant(value=節.真)
        if isinstance(節, 其值):
            return ast.Call(
                func=ast.Name(id=self._其函名, ctx=ast.Load()), args=[], keywords=[]
            )
        if isinstance(節, 其餘值):
            self._拋出文法錯誤("其餘不可獨立成值", 節.位置.start)
        self._拋出文法錯誤("不識之值", 節.位置.start)
        raise AssertionError("unreachable")

    def _轉條件原子(self, 原子: 條件原子) -> ast.expr:
        基 = self._轉值(原子.值)
        if 原子.之長:
            return ast.Call(
                func=ast.Name(id="len", ctx=ast.Load()), args=[基], keywords=[]
            )
        if 原子.下標 is None:
            return 基
        索 = 原子.下標
        if isinstance(索, 其餘值):
            return ast.Subscript(
                value=基,
                slice=ast.Slice(lower=ast.Constant(value=1), upper=None, step=None),
                ctx=ast.Load(),
            )
        索引 = self._轉下標索引(索)
        return ast.Call(
            func=ast.Name(id="取物", ctx=ast.Load()),
            args=[基, 索引],
            keywords=[],
        )

    def _轉下標索引(self, 索: 值) -> ast.expr:
        if isinstance(索, 言值):
            return ast.Constant(value=_還原言值(索.文))
        if isinstance(索, 數值):
            try:
                return ast.Constant(value=int(float(索.文)))
            except ValueError:
                self._拋出文法錯誤("非法下標", 索.位置.start)
        索式 = self._轉值(索)
        return ast.Call(
            func=ast.Name(id="文言轉整", ctx=ast.Load()),
            args=[索式, ast.Constant(value=0)],
            keywords=[],
        )

    def _轉條件式(self, 片段: list[條件原子 | str], 反轉: bool) -> ast.expr:
        if not 片段:
            試 = ast.Constant(value=False)
            return ast.UnaryOp(op=ast.Not(), operand=試) if 反轉 else 試

        序: list[ast.expr | str] = []
        for 項 in 片段:
            if isinstance(項, str):
                序.append(項)
            else:
                序.append(self._轉條件原子(項))

        # 以 ||/&& 分段；段內只含比較運算（或單一值）。
        段列: list[list[ast.expr | str]] = []
        邏輯列: list[str] = []
        當前: list[ast.expr | str] = []
        for 項 in 序:
            if isinstance(項, str) and 項 in {"||", "&&"}:
                段列.append(當前)
                邏輯列.append(項)
                當前 = []
            else:
                當前.append(項)
        段列.append(當前)

        def 段轉(段: list[ast.expr | str]) -> ast.expr:
            if not 段:
                return ast.Constant(value=False)
            if len(段) == 1:
                return 段[0]  # type: ignore[return-value]
            if len(段) % 2 == 0:
                self._拋出文法錯誤("條件式不完整", 0)
            左 = 段[0]
            if isinstance(左, str):
                self._拋出文法錯誤("條件式不合法", 0)
            比較運算子列: list[ast.cmpop] = []
            比較對象列: list[ast.expr] = []
            for i in range(1, len(段), 2):
                op = 段[i]
                右 = 段[i + 1]
                if isinstance(op, str):
                    if op == "==":
                        比較運算子列.append(ast.Eq())
                    elif op == "!=":
                        比較運算子列.append(ast.NotEq())
                    elif op == "<=":
                        比較運算子列.append(ast.LtE())
                    elif op == ">=":
                        比較運算子列.append(ast.GtE())
                    elif op == "<":
                        比較運算子列.append(ast.Lt())
                    elif op == ">":
                        比較運算子列.append(ast.Gt())
                    else:
                        self._拋出文法錯誤("未知比較", 0)
                else:
                    self._拋出文法錯誤("比較符非法", 0)
                if isinstance(右, str):
                    self._拋出文法錯誤("比較式不合法", 0)
                比較對象列.append(右)
            return ast.Compare(left=左, ops=比較運算子列, comparators=比較對象列)

        段式列 = [段轉(段) for 段 in 段列]

        # && 優先於 ||
        或段: list[ast.expr] = []
        當前且: list[ast.expr] = [段式列[0]]
        for i, 邏 in enumerate(邏輯列):
            下一 = 段式列[i + 1]
            if 邏 == "&&":
                當前且.append(下一)
            else:
                或段.append(
                    當前且[0]
                    if len(當前且) == 1
                    else ast.BoolOp(op=ast.And(), values=當前且)
                )
                當前且 = [下一]
        或段.append(
            當前且[0] if len(當前且) == 1 else ast.BoolOp(op=ast.And(), values=當前且)
        )
        試 = 或段[0] if len(或段) == 1 else ast.BoolOp(op=ast.Or(), values=或段)
        return ast.UnaryOp(op=ast.Not(), operand=試) if 反轉 else 試

    def _填體(self, 體: list[ast.stmt]) -> list[ast.stmt]:
        return 體 if 體 else [ast.Pass()]

    def _轉句列(self, 句列: list[句]) -> list[ast.stmt]:
        主體: list[ast.stmt] = []
        for 句節 in 句列:
            主體.extend(self._轉句(句節))
        if self._待取數 is not None or self._待取其餘:
            索引 = 句列[-1].位置.stop if 句列 else 0
            self._拋出文法錯誤("取後未以施", 索引)
        return 主體

    def _轉句(self, 節: 句) -> list[ast.stmt]:
        if (self._待取數 is not None or self._待取其餘) and not isinstance(
            節, (以施句, 取句, 註釋句, 宏句)
        ):
            self._拋出文法錯誤("取後需以施", 節.位置.start)
        if isinstance(節, 匯入句):
            return self._轉匯入句(節)

        if isinstance(節, 術定義句):
            self._檢名(節.名, 節.位置)
            固定參列: list[術參數] = []
            其餘參: 術參數 | None = None
            for 參 in 節.參數列:
                self._檢名(參.名, 節.位置)
                if 參.其餘:
                    if 其餘參 is None:
                        其餘參 = 參
                else:
                    固定參列.append(參)
            本參數列 = [ast.arg(arg=參.名, annotation=None) for 參 in 固定參列]
            if 其餘參 is not None:
                本參數列.append(ast.arg(arg=其餘參.名, annotation=None))
            原待取 = self._待取數
            原待取其餘 = self._待取其餘
            self._待取數 = None
            self._待取其餘 = False
            原體 = self._轉句列(節.體)
            self._待取數 = 原待取
            self._待取其餘 = 原待取其餘
            原體 = self._填體(原體)
            宣告列: list[ast.stmt] = []
            資訊 = self._作用域資訊.get(id(節))
            全域名 = set(資訊.全域) if 資訊 is not None else set()
            非區名 = set(資訊.非區) if 資訊 is not None else set()
            全域名.add(self._暫存名)
            if 全域名:
                宣告列.append(ast.Global(names=sorted(全域名)))
            if 非區名:
                宣告列.append(ast.Nonlocal(names=sorted(非區名)))
            暫名 = self._新內部名("暫存")
            初始化 = [
                ast.Assign(
                    targets=[ast.Name(id=暫名, ctx=ast.Store())],
                    value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                ),
                ast.Assign(
                    targets=[ast.Name(id=self._暫存名, ctx=ast.Store())],
                    value=ast.List(elts=[], ctx=ast.Load()),
                ),
            ]
            復原 = ast.Assign(
                targets=[ast.Name(id=self._暫存名, ctx=ast.Store())],
                value=ast.Name(id=暫名, ctx=ast.Load()),
            )
            體 = (
                宣告列
                + 初始化
                + [ast.Try(body=原體, handlers=[], orelse=[], finalbody=[復原])]
            )
            本名 = self._新內部名("術本")
            本函 = ast.FunctionDef(
                name=本名,
                args=ast.arguments(
                    posonlyargs=[],
                    args=本參數列,
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=體,
                decorator_list=[],
                returns=None,
                type_comment=None,
            )
            群名 = self._新內部名("參群")
            已名 = self._新內部名("已")
            結名 = self._新內部名("結")
            後名 = self._新內部名("後群")
            續名 = self._新內部名("續")
            需數 = len(固定參列)
            接其餘 = 其餘參 is not None

            if 接其餘:
                呼本參列: list[ast.expr] = []
                if 需數 > 0:
                    呼本參列.append(
                        ast.Starred(
                            value=ast.Subscript(
                                value=ast.Name(id=群名, ctx=ast.Load()),
                                slice=ast.Slice(
                                    lower=None,
                                    upper=ast.Constant(value=需數),
                                    step=None,
                                ),
                                ctx=ast.Load(),
                            ),
                            ctx=ast.Load(),
                        )
                    )
                呼本參列.append(
                    ast.Call(
                        func=ast.Name(id="list", ctx=ast.Load()),
                        args=[
                            ast.Subscript(
                                value=ast.Name(id=群名, ctx=ast.Load()),
                                slice=ast.Slice(
                                    lower=ast.Constant(value=需數),
                                    upper=None,
                                    step=None,
                                ),
                                ctx=ast.Load(),
                            )
                        ],
                        keywords=[],
                    )
                )
                滿足體: list[ast.stmt] = [
                    ast.Return(
                        value=ast.Call(
                            func=ast.Name(id=本名, ctx=ast.Load()),
                            args=呼本參列,
                            keywords=[],
                        )
                    )
                ]
            else:
                滿足體 = [
                    ast.Assign(
                        targets=[ast.Name(id=結名, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Name(id=本名, ctx=ast.Load()),
                            args=[
                                ast.Starred(
                                    value=ast.Subscript(
                                        value=ast.Name(id=群名, ctx=ast.Load()),
                                        slice=ast.Slice(
                                            lower=None,
                                            upper=ast.Constant(value=需數),
                                            step=None,
                                        ),
                                        ctx=ast.Load(),
                                    ),
                                    ctx=ast.Load(),
                                )
                            ],
                            keywords=[],
                        ),
                    ),
                    ast.If(
                        test=ast.Compare(
                            left=ast.Name(id=已名, ctx=ast.Load()),
                            ops=[ast.Eq()],
                            comparators=[ast.Constant(value=需數)],
                        ),
                        body=[ast.Return(value=ast.Name(id=結名, ctx=ast.Load()))],
                        orelse=[
                            ast.Return(
                                value=ast.Call(
                                    func=ast.Name(id="__文言呼叫", ctx=ast.Load()),
                                    args=[
                                        ast.Name(id=結名, ctx=ast.Load()),
                                        ast.Starred(
                                            value=ast.Subscript(
                                                value=ast.Name(id=群名, ctx=ast.Load()),
                                                slice=ast.Slice(
                                                    lower=ast.Constant(value=需數),
                                                    upper=None,
                                                    step=None,
                                                ),
                                                ctx=ast.Load(),
                                            ),
                                            ctx=ast.Load(),
                                        ),
                                    ],
                                    keywords=[],
                                )
                            )
                        ],
                    ),
                ]

            包函 = ast.FunctionDef(
                name=節.名,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    vararg=ast.arg(arg=群名, annotation=None),
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id=已名, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Name(id="len", ctx=ast.Load()),
                            args=[ast.Name(id=群名, ctx=ast.Load())],
                            keywords=[],
                        ),
                    ),
                    ast.If(
                        test=ast.Compare(
                            left=ast.Name(id=已名, ctx=ast.Load()),
                            ops=[ast.GtE()],
                            comparators=[ast.Constant(value=需數)],
                        ),
                        body=滿足體,
                        orelse=[
                            ast.FunctionDef(
                                name=續名,
                                args=ast.arguments(
                                    posonlyargs=[],
                                    args=[],
                                    vararg=ast.arg(arg=後名, annotation=None),
                                    kwonlyargs=[],
                                    kw_defaults=[],
                                    kwarg=None,
                                    defaults=[],
                                ),
                                body=[
                                    ast.Return(
                                        value=ast.Call(
                                            func=ast.Name(id="__文言呼叫", ctx=ast.Load()),
                                            args=[
                                                ast.Name(id=節.名, ctx=ast.Load()),
                                                ast.Starred(
                                                    value=ast.BinOp(
                                                        left=ast.Name(id=群名, ctx=ast.Load()),
                                                        op=ast.Add(),
                                                        right=ast.Name(id=後名, ctx=ast.Load()),
                                                    ),
                                                    ctx=ast.Load(),
                                                ),
                                            ],
                                            keywords=[],
                                        )
                                    )
                                ],
                                decorator_list=[],
                                returns=None,
                                type_comment=None,
                            ),
                            ast.Return(value=ast.Name(id=續名, ctx=ast.Load())),
                        ],
                    ),
                ],
                decorator_list=[],
                returns=None,
                type_comment=None,
            )
            設本參 = ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id=本名, ctx=ast.Load()),
                        attr="__文言術參數數__",
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=需數),
            )
            設包參 = ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id=節.名, ctx=ast.Load()),
                        attr="__文言術參數數__",
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=需數),
            )
            設本餘 = ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id=本名, ctx=ast.Load()),
                        attr="__文言術接其餘__",
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=接其餘),
            )
            設包餘 = ast.Assign(
                targets=[
                    ast.Attribute(
                        value=ast.Name(id=節.名, ctx=ast.Load()),
                        attr="__文言術接其餘__",
                        ctx=ast.Store(),
                    )
                ],
                value=ast.Constant(value=接其餘),
            )
            return [本函, 包函, 設本參, 設包參, 設本餘, 設包餘]
        if isinstance(節, 宣告句):
            結果: list[ast.stmt] = []
            for i in range(節.數量):
                值節 = 節.初值列[i] if i < len(節.初值列) else None
                if 值節 is None:
                    if 節.類型 == "數":
                        值式 = ast.Constant(value=0)
                    elif 節.類型 == "言":
                        值式 = ast.Constant(value="")
                    elif 節.類型 == "爻":
                        值式 = ast.Constant(value=False)
                    elif 節.類型 == "列":
                        值式 = ast.List(elts=[], ctx=ast.Load())
                    elif 節.類型 == "物":
                        值式 = ast.Dict(keys=[], values=[])
                    elif 節.類型 == "元":
                        值式 = ast.Constant(value=None)
                    elif 節.類型 == "術":
                        值式 = ast.Lambda(
                            args=ast.arguments(
                                posonlyargs=[],
                                args=[],
                                vararg=None,
                                kwonlyargs=[],
                                kw_defaults=[],
                                kwarg=None,
                                defaults=[],
                            ),
                            body=ast.Constant(value=0),
                        )
                    else:
                        值式 = ast.Constant(value=None)
                else:
                    值式 = self._轉值(值節)
                if i < len(節.名列):
                    名 = 節.名列[i]
                    self._檢名(名, 節.位置)
                    結果.append(
                        ast.Assign(
                            targets=[ast.Name(id=名, ctx=ast.Store())], value=值式
                        )
                    )
                else:
                    結果.append(
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                                    attr="append",
                                    ctx=ast.Load(),
                                ),
                                args=[值式],
                                keywords=[],
                            )
                        )
                    )
            return 結果

        if isinstance(節, 初始化句):
            值式 = self._轉值(節.初值)
            if 節.名 is not None:
                self._檢名(節.名, 節.位置)
                return [
                    ast.Assign(
                        targets=[ast.Name(id=節.名, ctx=ast.Store())], value=值式
                    )
                ]
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[值式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 命名句):
            結果: list[ast.stmt] = []
            for 名 in reversed(節.名列):
                self._檢名(名, 節.位置)
                結果.append(
                    ast.Assign(
                        targets=[ast.Name(id=名, ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                                attr="pop",
                                ctx=ast.Load(),
                            ),
                            args=[],
                            keywords=[],
                        ),
                    )
                )
            return 結果

        if isinstance(節, 施句):
            呼 = ast.Call(
                func=self._轉值(節.術),
                args=[self._轉值(參) for 參 in 節.參數列],
                keywords=[],
            )
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[呼],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 以施句):
            if self._待取數 is None and not self._待取其餘:
                self._拋出文法錯誤("以施需先取", 節.位置.start)
            數量 = self._待取數
            取其餘 = self._待取其餘
            self._待取數 = None
            self._待取其餘 = False
            if 取其餘:
                取值呼 = ast.Call(
                    func=ast.Name(id="__取其餘", ctx=ast.Load()), args=[], keywords=[]
                )
            else:
                assert 數量 is not None
                取值呼 = ast.Call(
                    func=ast.Name(id="__取", ctx=ast.Load()),
                    args=[ast.Constant(value=數量)],
                    keywords=[],
                )
            呼 = ast.Call(
                func=self._轉值(節.術),
                args=[
                    ast.Starred(
                        value=取值呼,
                        ctx=ast.Load(),
                    ),
                ],
                keywords=[],
            )
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[呼],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 取句):
            self._待取其餘 = 節.其餘
            self._待取數 = None if 節.其餘 else 節.數量
            return []

        if isinstance(節, 返回句):
            if 節.空無:
                return [ast.Return(value=ast.Constant(value=None))]
            if 節.取棧:
                return [
                    ast.Return(
                        value=ast.Call(
                            func=ast.Name(id=self._其函名, ctx=ast.Load()),
                            args=[],
                            keywords=[],
                        )
                    )
                ]
            if 節.值 is None:
                return [ast.Return(value=None)]
            return [ast.Return(value=self._轉值(節.值))]

        if isinstance(節, 列充句):
            列式 = self._轉值(節.列)
            if not isinstance(列式, ast.Name):
                暫名 = self._新內部名("列")
                暫存指派 = ast.Assign(
                    targets=[ast.Name(id=暫名, ctx=ast.Store())], value=列式
                )
                列式 = ast.Name(id=暫名, ctx=ast.Load())
                結果: list[ast.stmt] = [暫存指派]
            else:
                結果 = []
            for 值節 in 節.值列:
                結果.append(
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=列式, attr="append", ctx=ast.Load()
                            ),
                            args=[self._轉值(值節)],
                            keywords=[],
                        )
                    )
                )
            return 結果

        if isinstance(節, 列銜句):
            列列 = [self._轉值(節.列)] + [self._轉值(列) for 列 in 節.列列]
            式 = 列列[0]
            for 右 in 列列[1:]:
                式 = ast.BinOp(left=式, op=ast.Add(), right=右)
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 物定義句):
            self._檢名(節.名, 節.位置)
            keys = [self._轉值(屬.鍵) for 屬 in 節.屬性列]
            values = [self._轉值(屬.值) for 屬 in 節.屬性列]
            return [
                ast.Assign(
                    targets=[ast.Name(id=節.名, ctx=ast.Store())],
                    value=ast.Dict(keys=keys, values=values),
                )
            ]

        if isinstance(節, 凡句):
            self._檢名(節.變數名, 節.位置)
            體 = self._填體(self._轉句列(節.體))
            return [
                ast.For(
                    target=ast.Name(id=節.變數名, ctx=ast.Store()),
                    iter=self._轉值(節.容器),
                    body=體,
                    orelse=[],
                )
            ]

        if isinstance(節, 試句):
            體 = self._填體(self._轉句列(節.體))
            if not 節.捕捉列:
                handlers = [
                    ast.ExceptHandler(
                        type=ast.Name(id="文言之禍", ctx=ast.Load()),
                        name=None,
                        body=[ast.Pass()],
                    )
                ]
                return [ast.Try(body=體, handlers=handlers, orelse=[], finalbody=[])]
            禍名 = self._新內部名("禍")
            鏈: ast.stmt | None = None
            尾: ast.If | None = None
            捕尾體: list[ast.stmt] | None = None
            for 捕 in 節.捕捉列:
                子體 = self._填體(self._轉句列(捕.體))
                if 捕.變數名 is not None:
                    self._檢名(捕.變數名, 節.位置)
                    子體 = [
                        ast.Assign(
                            targets=[ast.Name(id=捕.變數名, ctx=ast.Store())],
                            value=ast.Name(id=禍名, ctx=ast.Load()),
                        )
                    ] + 子體
                if 捕.亦可:
                    捕尾體 = 子體
                    break
                if 捕.錯名 is None:
                    self._拋出文法錯誤("捕捉需錯名", 節.位置.start)
                測 = ast.Compare(
                    left=ast.Attribute(
                        value=ast.Name(id=禍名, ctx=ast.Load()),
                        attr="名",
                        ctx=ast.Load(),
                    ),
                    ops=[ast.Eq()],
                    comparators=[self._轉值(捕.錯名)],
                )
                節點 = ast.If(test=測, body=子體, orelse=[])
                if 鏈 is None:
                    鏈 = 節點
                else:
                    assert 尾 is not None
                    尾.orelse = [節點]
                尾 = 節點
            if 捕尾體 is None:
                捕尾體 = [ast.Pass()]
            if 鏈 is None:
                處理體 = 捕尾體
            else:
                assert 尾 is not None
                尾.orelse = 捕尾體
                處理體 = [鏈]
            handlers = [
                ast.ExceptHandler(
                    type=ast.Name(id="文言之禍", ctx=ast.Load()), name=禍名, body=處理體
                )
            ]
            return [ast.Try(body=體, handlers=handlers, orelse=[], finalbody=[])]

        if isinstance(節, 擲句):
            args = [self._轉值(節.名)]
            if 節.訊 is not None:
                args.append(self._轉值(節.訊))
            return [
                ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="文言之禍", ctx=ast.Load()),
                        args=args,
                        keywords=[],
                    ),
                    cause=None,
                )
            ]

        if isinstance(節, 註釋句):
            return []

        if isinstance(節, 宏句):
            return []

        if isinstance(節, 書之句):
            呼 = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[
                        ast.Starred(
                            value=ast.Call(
                                func=ast.Name(id="__文言輸出列", ctx=ast.Load()),
                                args=[ast.Name(id=self._暫存名, ctx=ast.Load())],
                                keywords=[],
                            ),
                            ctx=ast.Load(),
                        )
                    ],
                    keywords=[],
                )
            )
            清 = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                        attr="clear",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                )
            )
            return [呼, 清]

        if isinstance(節, 噫句):
            清 = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(
                        value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                        attr="clear",
                        ctx=ast.Load(),
                    ),
                    args=[],
                    keywords=[],
                )
            )
            return [清]

        if isinstance(節, 算術句):
            左 = self._轉值(節.左)
            右 = self._轉值(節.右)
            if 節.算 in {"+", "-", "*", "/", "%"}:
                運算對照 = {
                    "+": ast.Add(),
                    "-": ast.Sub(),
                    "*": ast.Mult(),
                    "/": ast.Div(),
                    "%": ast.Mod(),
                }
                式 = ast.BinOp(left=左, op=運算對照[節.算], right=右)
            elif 節.算 in {"||", "&&"}:
                式 = ast.BoolOp(
                    op=ast.Or() if 節.算 == "||" else ast.And(), values=[左, 右]
                )
            else:
                self._拋出文法錯誤("未知運算", 節.位置.start)
                raise AssertionError("unreachable")
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 變句):
            式 = ast.UnaryOp(op=ast.Not(), operand=self._轉值(節.值))
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 夫句):
            式 = self._轉值(節.值)
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 之長句):
            式 = ast.Call(
                func=ast.Name(id="len", ctx=ast.Load()),
                args=[self._轉值(節.容器)],
                keywords=[],
            )
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 之句):
            原 = 條件原子(節.位置, 節.容器, 節.索引, False)
            式 = self._轉條件原子(原)
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            attr="append",
                            ctx=ast.Load(),
                        ),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 昔今句):
            self._檢名(節.左名, 節.位置)
            前置: list[ast.stmt] = []
            左索為言 = False
            if 節.左下標 is None:
                目標: ast.expr = ast.Name(id=節.左名, ctx=ast.Store())
                索 = None
            else:
                if isinstance(節.左下標, 其餘值):
                    self._拋出文法錯誤("不可對其餘賦值", 節.位置.start)
                左索為言 = isinstance(節.左下標, 言值)
                索名 = self._新內部名("索")
                前置.append(
                    ast.Assign(
                        targets=[ast.Name(id=索名, ctx=ast.Store())],
                        value=self._轉下標索引(節.左下標),
                    )
                )
                索 = ast.Name(id=索名, ctx=ast.Load())
                索式 = 索 if 左索為言 else ast.BinOp(left=索, op=ast.Sub(), right=ast.Constant(value=1))
                目標 = ast.Subscript(
                    value=ast.Name(id=節.左名, ctx=ast.Load()),
                    slice=_造索引(索式),
                    ctx=ast.Store(),
                )

            if 節.刪除:
                if 節.左下標 is None:
                    return [
                        ast.Assign(
                            targets=[ast.Name(id=節.左名, ctx=ast.Store())],
                            value=ast.Constant(value=None),
                        )
                    ]
                if 索 is None:
                    self._拋出文法錯誤("缺左下標", 節.位置.start)
                return 前置 + [
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Name(id="刪物", ctx=ast.Load()),
                            args=[ast.Name(id=節.左名, ctx=ast.Load()), 索],
                            keywords=[],
                        )
                    )
                ]

            if 節.右值 is None:
                self._拋出文法錯誤("缺右值", 節.位置.start)
            右式: ast.expr = self._轉值(節.右值)
            if 節.右下標 is not None:
                原右 = 條件原子(節.位置, 節.右值, 節.右下標, False)
                右式 = self._轉條件原子(原右)
            if 節.左下標 is None:
                return 前置 + [ast.Assign(targets=[目標], value=右式)]
            if 左索為言:
                return 前置 + [
                    ast.Try(
                        body=[ast.Assign(targets=[目標], value=右式)],
                        handlers=[
                            ast.ExceptHandler(
                                type=ast.Name(id="Exception", ctx=ast.Load()),
                                name=None,
                                body=[ast.Pass()],
                            )
                        ],
                        orelse=[],
                        finalbody=[],
                    )
                ]

            return 前置 + [
                ast.If(
                    test=ast.BoolOp(
                        op=ast.And(),
                        values=[
                            ast.Call(
                                func=ast.Name(id="isinstance", ctx=ast.Load()),
                                args=[
                                    ast.Name(id=節.左名, ctx=ast.Load()),
                                    ast.Name(id="list", ctx=ast.Load()),
                                ],
                                keywords=[],
                            ),
                            ast.Compare(
                                left=索,
                                ops=[ast.LtE()],
                                comparators=[ast.Constant(value=0)],
                            ),
                        ],
                    ),
                    body=[
                        ast.Assign(
                            targets=[
                                ast.Subscript(
                                    value=ast.Name(id="__文言負索", ctx=ast.Load()),
                                    slice=_造索引(
                                        ast.Tuple(
                                            elts=[
                                                ast.Call(
                                                    func=ast.Name(id="id", ctx=ast.Load()),
                                                    args=[ast.Name(id=節.左名, ctx=ast.Load())],
                                                    keywords=[],
                                                ),
                                                索,
                                            ],
                                            ctx=ast.Load(),
                                        )
                                    ),
                                    ctx=ast.Store(),
                                )
                            ],
                            value=右式,
                        )
                    ],
                    orelse=[
                        ast.If(
                            test=ast.BoolOp(
                                op=ast.And(),
                                values=[
                                    ast.Call(
                                        func=ast.Name(id="isinstance", ctx=ast.Load()),
                                        args=[
                                            ast.Name(id=節.左名, ctx=ast.Load()),
                                            ast.Name(id="list", ctx=ast.Load()),
                                        ],
                                        keywords=[],
                                    ),
                                    ast.Compare(
                                        left=索,
                                        ops=[ast.Gt()],
                                        comparators=[
                                            ast.Call(
                                                func=ast.Name(id="len", ctx=ast.Load()),
                                                args=[ast.Name(id=節.左名, ctx=ast.Load())],
                                                keywords=[],
                                            )
                                        ],
                                    ),
                                ],
                            ),
                            body=[
                                ast.Expr(
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id=節.左名, ctx=ast.Load()),
                                            attr="extend",
                                            ctx=ast.Load(),
                                        ),
                                        args=[
                                            ast.BinOp(
                                                left=ast.List(
                                                    elts=[ast.Constant(value=None)],
                                                    ctx=ast.Load(),
                                                ),
                                                op=ast.Mult(),
                                                right=ast.BinOp(
                                                    left=索,
                                                    op=ast.Sub(),
                                                    right=ast.Call(
                                                        func=ast.Name(id="len", ctx=ast.Load()),
                                                        args=[
                                                            ast.Name(
                                                                id=節.左名, ctx=ast.Load()
                                                            )
                                                        ],
                                                        keywords=[],
                                                    ),
                                                ),
                                            )
                                        ],
                                        keywords=[],
                                    )
                                )
                            ],
                            orelse=[],
                        ),
                        ast.Assign(targets=[目標], value=右式),
                    ],
                )
            ]

        if isinstance(節, 若句):
            試 = self._轉條件式(節.條件, 節.反轉)
            然體 = self._填體(self._轉句列(節.然))
            否體: list[ast.stmt] = self._轉句列(節.否則)

            下個: list[ast.stmt] = self._填體(否體) if 否體 else []
            for 子 in reversed(節.另若列):
                子試 = self._轉條件式(子.條件, False)
                子體 = self._填體(self._轉句列(子.體))
                下個 = [ast.If(test=子試, body=子體, orelse=下個)]
            return [ast.If(test=試, body=然體, orelse=下個)]

        if isinstance(節, 恆為是句):
            體 = self._填體(self._轉句列(節.體))
            return [ast.While(test=ast.Constant(value=True), body=體, orelse=[])]

        if isinstance(節, 為是遍句):
            迭名 = self._新內部名("遍")
            體 = self._填體(self._轉句列(節.體))
            return [
                ast.For(
                    target=ast.Name(id=迭名, ctx=ast.Store()),
                    iter=ast.Call(
                        func=ast.Name(id="range", ctx=ast.Load()),
                        args=[self._轉值(節.次數)],
                        keywords=[],
                    ),
                    body=體,
                    orelse=[],
                )
            ]

        if isinstance(節, 乃止句):
            return [ast.Break()]

        if isinstance(節, 乃止是遍句):
            return [ast.Continue()]

        self._拋出文法錯誤("此句未支援", 節.位置.start)
        raise AssertionError("unreachable")

    def _轉匯入句(self, 節: 匯入句) -> list[ast.stmt]:
        路徑 = _解析模組路徑(節.模組, self.文檔名, self.內容, 節.位置, self._環境)
        if 路徑 in self._環境.已載入:
            return []
        if 路徑 in self._環境.編譯中:
            self._拋出文法錯誤("循環匯入", 節.位置.start)
        if 路徑 in self._環境.模組快取:
            self._環境.已載入.add(路徑)
            return self._環境.模組快取[路徑]
        self._環境.編譯中.add(路徑)
        try:
            原文 = _讀取源碼(路徑, self._環境)
            程, 處理後 = _解析前處理(原文, 路徑, self._環境)
            轉譯器 = PythonAST轉譯器(處理後, 路徑, self._環境, 插入序言=False)
            句列 = 轉譯器._轉譯句列(程)
            self._環境.模組快取[路徑] = 句列
            self._環境.已載入.add(路徑)
            return 句列
        finally:
            self._環境.編譯中.discard(路徑)


def 轉譯為PythonAST(
    程: 程式, 內容: str, 文檔名: str = "<言>", 環境: 編譯環境 | None = None
) -> ast.Module:
    """Wenyan AST → Python AST。"""

    return PythonAST轉譯器(內容, 文檔名, 環境=環境).轉譯(程)


def 編譯為PythonAST(內容: str, 文檔名: str = "<言>") -> ast.Module:
    """文言源碼 → Python AST（lexer → parser → transformer）。"""

    環境 = _建立編譯環境()
    程, 處理後 = _解析前處理(內容, 文檔名, 環境)
    return 轉譯為PythonAST(程, 處理後, 文檔名, 環境)


def 主術(參數列表: List[str] | None = None) -> int:
    """執行命令列入口。

    Args:
        參數列表: 參數列表；None 表示使用 sys.argv[1:]。

    Returns:
        結束碼。
    """

    參數 = sys.argv[1:] if 參數列表 is None else 參數列表

    def 顯示說明() -> None:
        print("用法：wenyan [--tokens|--wyast|--pyast] [--no-outputHanzi] <檔案.wy|-> ...")
        print("  預設：編譯為 Python AST 並執行。")
        print("  --tokens：僅輸出詞法符號（debug）。")
        print("  --wyast：輸出 Wenyan AST（debug）。")
        print("  --pyast：輸出 Python AST dump（debug）。")
        print("  --no-outputHanzi：執行模式輸出阿拉伯數字（與 @wenyan/cli 相容）。")

    if not 參數:
        顯示說明()
        return 0

    模式 = "exec"
    不輸出漢字 = False
    while 參數 and 參數[0] != "-":
        選項 = 參數[0]
        if 選項 in {"-h", "--help"}:
            顯示說明()
            return 0
        if 選項 in {"--tokens", "--lex"}:
            模式 = "tokens"
            參數 = 參數[1:]
            continue
        if 選項 in {"--wyast"}:
            模式 = "wyast"
            參數 = 參數[1:]
            continue
        if 選項 in {"--pyast", "--ast"}:
            模式 = "pyast"
            參數 = 參數[1:]
            continue
        if 選項 == "--no-outputHanzi":
            不輸出漢字 = True
            參數 = 參數[1:]
            continue
        if 選項.startswith("-"):
            print(f"未知選項：{選項}", file=sys.stderr)
            return 2
        break

    if not 參數:
        print("未指定檔案。可用 -h/--help。", file=sys.stderr)
        return 2

    for 路徑 in 參數:
        try:
            if 路徑 == "-":
                內容 = sys.stdin.read()
                文檔名 = "<stdin>"
            else:
                with open(路徑, "r", encoding="utf-8") as 檔案:
                    內容 = 檔案.read()
                文檔名 = 路徑

            環境 = _建立編譯環境()
            if 模式 == "tokens":
                處理後 = _前處理源碼(內容, 文檔名, 環境)
                print(list(詞法分析器(處理後, 文檔名)))
                continue
            if 模式 == "wyast":
                程, _ = _解析前處理(內容, 文檔名, 環境)
                print(程)
                continue
            if 模式 == "pyast":
                程, 處理後 = _解析前處理(內容, 文檔名, 環境)
                模組樹 = 轉譯為PythonAST(程, 處理後, 文檔名, 環境)
                print(ast.dump(模組樹, include_attributes=True))
                continue

            程, 處理後 = _解析前處理(內容, 文檔名, 環境)
            模組樹 = 轉譯為PythonAST(程, 處理後, 文檔名, 環境)
            程式碼 = compile(模組樹, 文檔名, "exec")
            作用域 = {
                "__name__": "__main__",
                "__file__": 文檔名,
                "__wenyan_no_output_hanzi__": 不輸出漢字,
            }
            exec(程式碼, 作用域, 作用域)
        except 文法之禍 as 錯:
            檔名 = getattr(錯, "filename", "<言>") or "<言>"
            行號 = getattr(錯, "lineno", 0) or 0
            列偏移 = getattr(錯, "offset", 0) or 0
            行文 = getattr(錯, "text", None)
            訊息 = getattr(錯, "msg", str(錯))
            print(f"{檔名}:{行號}:{列偏移}: {訊息}", file=sys.stderr)
            if isinstance(行文, str) and 行文:
                行文 = 行文.rstrip("\n")
                print(行文, file=sys.stderr)
                if 列偏移 > 0:
                    print(" " * (列偏移 - 1) + "^", file=sys.stderr)
            return 1
        except OSError as 錯:
            print(f"{路徑}: {錯}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(主術())
