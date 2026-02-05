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
    "文法分析器",
    "解析",
    "轉譯為PythonAST",
    "編譯為PythonAST",
]
版本號 = "0.1.0"

忽略符號 = frozenset({"。", "、", " ", "\t", "\n", "\r"})

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
                yield 符號("言", 文字, slice(索引, 結束))
                索引 = 結束
                continue

            字 = 內容[索引]
            if 字 in 忽略符號:
                if 數據起點 is None:
                    索引 += 1
                else:
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
        if 內容.startswith("「「", 起點):
            起始長度 = 2
        else:
            起始長度 = 1
        索引 = 起點 + 起始長度
        內容片段: List[str] = []
        層級 = 1
        while 索引 < len(內容):
            if 內容.startswith("「「", 索引):
                層級 += 1
                內容片段.append("「「")
                索引 += 2
                continue
            if 內容.startswith("『", 索引):
                層級 += 1
                內容片段.append("『")
                索引 += 1
                continue
            if 內容.startswith("」」", 索引):
                層級 -= 1
                if 層級 == 0:
                    索引 += 2
                    文字 = "".join(內容片段)
                    文字 = 文字.replace('"', '\\"').replace("\n", "\\n")
                    return 文字, 索引
                內容片段.append("」」")
                索引 += 2
                continue
            if 內容.startswith("』", 索引):
                層級 -= 1
                if 層級 == 0:
                    索引 += 1
                    文字 = "".join(內容片段)
                    文字 = 文字.replace('"', '\\"').replace("\n", "\\n")
                    return 文字, 索引
                內容片段.append("』")
                索引 += 1
                continue
            內容片段.append(內容[索引])
            索引 += 1
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

        if self._是關鍵詞(符, "吾有") or self._是關鍵詞(符, "今有"):
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
        if self._是關鍵詞(符, "若") or self._是關鍵詞(符, "若其然者") or self._是關鍵詞(符, "若其不然者"):
            return self._解析若句()
        if self._是關鍵詞(符, "恆為是"):
            return self._解析恆為是句()
        if self._是關鍵詞(符, "為是"):
            return self._解析為是遍句()
        if self._是關鍵詞(符, "乃止"):
            開 = self._取()
            return 乃止句(開.位置)
        if self._是關鍵詞(符, "乃止是遍"):
            開 = self._取()
            return 乃止是遍句(開.位置)
        if self._是關鍵詞(符, "云云") or self._是關鍵詞(符, "也"):
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
            return 之句(位置, 甲, 索)
        if self._是關鍵詞(self._看(), "之長"):
            之長符 = self._取()
            位置 = slice(開.位置.start, 之長符.位置.stop)
            return 之長句(位置, 甲)
        # 邏輯二元：夫 <甲> <乙> 中有陽乎/中無陰乎
        符 = self._看()
        若可值 = 符 is not None and (
            (符.類别 in {"名", "言", "數"} and 符.值 is not None)
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
                return 算術句(位置, 運, 甲, 乙)
            # 回退：非邏輯二元，視為僅取值
            self._索引 -= 1
        位置 = slice(開.位置.start, 甲.位置.stop)
        return 夫句(位置, 甲)

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
            位置 = slice(開.位置.start, 終.位置.stop)
            return 昔今句(位置, 左名, 左下標, None, None, True)
        右值 = self._解析值()
        右下標: 值 | None = None
        if self._是關鍵詞(self._看(), "之"):
            self._取()
            右下標 = self._解析值()
        終 = self._期("是矣")
        位置 = slice(開.位置.start, 終.位置.stop)
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
        然 = self._解析語句列(終止詞=frozenset({"或若", "若非", "云云", "也"}))
        另若列: list[或若子句] = []
        while self._是關鍵詞(self._看(), "或若"):
            或若開 = self._取()
            或若條 = self._解析條件式()
            self._期("者")
            或若體 = self._解析語句列(終止詞=frozenset({"或若", "若非", "云云", "也"}))
            終 = self.符號列[self._索引 - 1]
            另若列.append(或若子句(slice(或若開.位置.start, 終.位置.stop), 或若條, 或若體))
        否則: list[句] = []
        if self._是關鍵詞(self._看(), "若非"):
            self._取()
            否則 = self._解析語句列(終止詞=frozenset({"云云", "也"}))
        終結 = self._看()
        if 終結 is None or not (self._是關鍵詞(終結, "云云") or self._是關鍵詞(終結, "也")):
            self._拋出文法錯誤("若未終", 開.位置.start)
        終符 = self._取()
        位置 = slice(開.位置.start, 終符.位置.stop)
        return 若句(位置, 條件, 反轉, 然, 另若列, 否則)

    def _解析恆為是句(self) -> 恆為是句:
        開 = self._期("恆為是")
        體 = self._解析語句列(終止詞=frozenset({"云云", "也"}))
        終符 = self._取()
        if not (self._是關鍵詞(終符, "云云") or self._是關鍵詞(終符, "也")):
            self._拋出文法錯誤("循環未終", 終符.位置.start)
        位置 = slice(開.位置.start, 終符.位置.stop)
        return 恆為是句(位置, 體)

    def _解析為是遍句(self) -> 為是遍句:
        開 = self._期("為是")
        次數 = self._解析值()
        self._期("遍")
        體 = self._解析語句列(終止詞=frozenset({"云云", "也"}))
        終符 = self._取()
        if not (self._是關鍵詞(終符, "云云") or self._是關鍵詞(終符, "也")):
            self._拋出文法錯誤("循環未終", 終符.位置.start)
        位置 = slice(開.位置.start, 終符.位置.stop)
        return 為是遍句(位置, 次數, 體)


def 解析(內容: str, 文檔名: str = "<言>") -> 程式:
    """文言源碼轉 Wenyan AST。"""

    return 文法分析器(內容, 文檔名).解析程式()


def _還原言值(文: str) -> str:
    """將 lexer 的最小轉義字串還原成真實字元。"""

    return 文.replace("\\n", "\n").replace('\\"', '"')


def _造索引(值: ast.expr) -> ast.slice:
    """建立 `ast.Subscript` 所需的 slice/index 相容表示。"""

    if hasattr(ast, "Index"):
        return ast.Index(value=值)  # type: ignore[attr-defined, return-value]
    return 值  # type: ignore[return-value]


class PythonAST轉譯器:
    """將 Wenyan AST 轉譯為 Python `ast`。"""

    def __init__(self, 內容: str, 文檔名: str = "<言>") -> None:
        self.內容 = 內容
        self.文檔名 = 文檔名
        self._內部序 = 0
        self._暫存名 = "__暫存"
        self._其函名 = "__其"

    def 轉譯(self, 程: 程式) -> ast.Module:
        """轉譯整個程式。"""

        其值名 = "__其值"
        主體: list[ast.stmt] = [
            ast.Assign(
                targets=[ast.Name(id=self._暫存名, ctx=ast.Store())],
                value=ast.List(elts=[], ctx=ast.Load()),
            ),
            ast.FunctionDef(
                name=self._其函名,
                args=ast.arguments(
                    posonlyargs=[],
                    args=[],
                    vararg=None,
                    kwonlyargs=[],
                    kw_defaults=[],
                    kwarg=None,
                    defaults=[],
                ),
                body=[
                    ast.Assign(
                        targets=[ast.Name(id=其值名, ctx=ast.Store())],
                        value=ast.Subscript(
                            value=ast.Name(id=self._暫存名, ctx=ast.Load()),
                            slice=_造索引(ast.Constant(value=-1)),
                            ctx=ast.Load(),
                        ),
                    ),
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="clear", ctx=ast.Load()
                            ),
                            args=[],
                            keywords=[],
                        )
                    ),
                    ast.Return(value=ast.Name(id=其值名, ctx=ast.Load())),
                ],
                decorator_list=[],
                returns=None,
                type_comment=None,
            ),
        ]
        主體.extend(self._轉句列(程.句列))
        模組 = ast.Module(body=主體, type_ignores=[])
        return ast.fix_missing_locations(模組)

    def _新內部名(self, 前綴: str) -> str:
        self._內部序 += 1
        名 = f"__{前綴}{self._內部序}"
        return 名 if 名.isidentifier() else f"__tmp{self._內部序}"

    def _拋出文法錯誤(self, 訊息: str, 索引: int) -> None:
        行號, 列偏移, 行文字 = 計算行列(self.內容, 索引)
        raise 文法之禍(訊息, (self.文檔名, 行號, 列偏移, 行文字))

    def _檢名(self, 名: str, 位置: slice) -> None:
        if not 名.isidentifier() or keyword.iskeyword(名):
            self._拋出文法錯誤("名不合 Python 識別字", 位置.start)

    def _轉值(self, 節: 值) -> ast.expr:
        if isinstance(節, 名值):
            self._檢名(節.名, 節.位置)
            return ast.Name(id=節.名, ctx=ast.Load())
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
            return ast.Call(func=ast.Name(id=self._其函名, ctx=ast.Load()), args=[], keywords=[])
        if isinstance(節, 其餘值):
            self._拋出文法錯誤("其餘不可獨立成值", 節.位置.start)
        self._拋出文法錯誤("不識之值", 節.位置.start)
        raise AssertionError("unreachable")

    def _轉條件原子(self, 原子: 條件原子) -> ast.expr:
        基 = self._轉值(原子.值)
        if 原子.之長:
            return ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[基], keywords=[])
        if 原子.下標 is None:
            return 基
        索 = 原子.下標
        if isinstance(索, 其餘值):
            return ast.Subscript(
                value=基,
                slice=ast.Slice(lower=ast.Constant(value=1), upper=None, step=None),
                ctx=ast.Load(),
            )
        索引 = self._轉值(索)
        if isinstance(索, 言值):
            片 = _造索引(索引)
        else:
            片 = _造索引(ast.BinOp(left=索引, op=ast.Sub(), right=ast.Constant(value=1)))
        return ast.Subscript(value=基, slice=片, ctx=ast.Load())

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
                或段.append(當前且[0] if len(當前且) == 1 else ast.BoolOp(op=ast.And(), values=當前且))
                當前且 = [下一]
        或段.append(當前且[0] if len(當前且) == 1 else ast.BoolOp(op=ast.And(), values=當前且))
        試 = 或段[0] if len(或段) == 1 else ast.BoolOp(op=ast.Or(), values=或段)
        return ast.UnaryOp(op=ast.Not(), operand=試) if 反轉 else 試

    def _填體(self, 體: list[ast.stmt]) -> list[ast.stmt]:
        return 體 if 體 else [ast.Pass()]

    def _轉句列(self, 句列: list[句]) -> list[ast.stmt]:
        主體: list[ast.stmt] = []
        for 句節 in 句列:
            主體.extend(self._轉句(句節))
        return 主體

    def _轉句(self, 節: 句) -> list[ast.stmt]:
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
                    結果.append(ast.Assign(targets=[ast.Name(id=名, ctx=ast.Store())], value=值式))
                else:
                    結果.append(
                        ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()
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
                return [ast.Assign(targets=[ast.Name(id=節.名, ctx=ast.Store())], value=值式)]
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
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
                                value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="pop", ctx=ast.Load()
                            ),
                            args=[],
                            keywords=[],
                        ),
                    )
                )
            return 結果

        if isinstance(節, 書之句):
            呼 = ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[ast.Starred(value=ast.Name(id=self._暫存名, ctx=ast.Load()), ctx=ast.Load())],
                    keywords=[],
                )
            )
            清 = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="clear", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                )
            )
            return [呼, 清]

        if isinstance(節, 噫句):
            清 = ast.Expr(
                value=ast.Call(
                    func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="clear", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                )
            )
            return [清]

        if isinstance(節, 算術句):
            左 = self._轉值(節.左)
            右 = self._轉值(節.右)
            if 節.算 in {"+", "-", "*", "/", "%"}:
                運算對照 = {"+": ast.Add(), "-": ast.Sub(), "*": ast.Mult(), "/": ast.Div(), "%": ast.Mod()}
                式 = ast.BinOp(left=左, op=運算對照[節.算], right=右)
            elif 節.算 in {"||", "&&"}:
                式 = ast.BoolOp(op=ast.Or() if 節.算 == "||" else ast.And(), values=[左, 右])
            else:
                self._拋出文法錯誤("未知運算", 節.位置.start)
                raise AssertionError("unreachable")
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
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
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
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
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 之長句):
            式 = ast.Call(func=ast.Name(id="len", ctx=ast.Load()), args=[self._轉值(節.容器)], keywords=[])
            return [
                ast.Expr(
                    value=ast.Call(
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
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
                        func=ast.Attribute(value=ast.Name(id=self._暫存名, ctx=ast.Load()), attr="append", ctx=ast.Load()),
                        args=[式],
                        keywords=[],
                    )
                )
            ]

        if isinstance(節, 昔今句):
            self._檢名(節.左名, 節.位置)
            if 節.左下標 is None:
                目標: ast.expr = ast.Name(id=節.左名, ctx=ast.Store())
            else:
                if isinstance(節.左下標, 其餘值):
                    self._拋出文法錯誤("不可對其餘賦值", 節.位置.start)
                索 = self._轉值(節.左下標)
                if isinstance(節.左下標, 言值):
                    片 = _造索引(索)
                else:
                    片 = _造索引(ast.BinOp(left=索, op=ast.Sub(), right=ast.Constant(value=1)))
                目標 = ast.Subscript(value=ast.Name(id=節.左名, ctx=ast.Load()), slice=片, ctx=ast.Store())

            if 節.刪除:
                if not isinstance(目標, ast.Subscript):
                    self._拋出文法錯誤("刪除需下標", 節.位置.start)
                return [ast.Delete(targets=[目標])]

            if 節.右值 is None:
                self._拋出文法錯誤("缺右值", 節.位置.start)
            右式: ast.expr = self._轉值(節.右值)
            if 節.右下標 is not None:
                原右 = 條件原子(節.位置, 節.右值, 節.右下標, False)
                右式 = self._轉條件原子(原右)
            return [ast.Assign(targets=[目標], value=右式)]

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
                    iter=ast.Call(func=ast.Name(id="range", ctx=ast.Load()), args=[self._轉值(節.次數)], keywords=[]),
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


def 轉譯為PythonAST(程: 程式, 內容: str, 文檔名: str = "<言>") -> ast.Module:
    """Wenyan AST → Python AST。"""

    return PythonAST轉譯器(內容, 文檔名).轉譯(程)


def 編譯為PythonAST(內容: str, 文檔名: str = "<言>") -> ast.Module:
    """文言源碼 → Python AST（lexer → parser → transformer）。"""

    程 = 解析(內容, 文檔名)
    return 轉譯為PythonAST(程, 內容, 文檔名)


def 主術(參數列表: List[str] | None = None) -> int:
    """執行命令列入口。

    Args:
        參數列表: 參數列表；None 表示使用 sys.argv[1:]。

    Returns:
        結束碼。
    """

    參數 = sys.argv[1:] if 參數列表 is None else 參數列表
    if not 參數:
        return 0
    for 路徑 in 參數:
        with open(路徑, "r", encoding="utf-8") as 檔案:
            內容 = 檔案.read()
        print(list(詞法分析器(內容, 路徑)))
    return 0


if __name__ == "__main__":
    sys.exit(主術())
