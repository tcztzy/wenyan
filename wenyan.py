# -*- coding: utf-8 -*-
"""Wenyan 詞法分析與數字轉換。"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple

__all__ = ["詞法分析器", "漢字數字", "漢字變數字", "主術", "符號", "文法之禍", "文法錯誤"]
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


def 主術(参數列表: List[str] | None = None) -> int:
    """執行命令列入口。

    Args:
        参數列表: 參數列表；None 表示使用 sys.argv[1:]。

    Returns:
        結束碼。
    """

    參數 = sys.argv[1:] if 参數列表 is None else 参數列表
    if not 參數:
        return 0
    for 路徑 in 參數:
        with open(路徑, "r", encoding="utf-8") as 檔案:
            內容 = 檔案.read()
        print(list(詞法分析器(內容, 路徑)))
    return 0


if __name__ == "__name__":
    import sys

    sys.exit(主術())
