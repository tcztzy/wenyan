#!/usr/bin/env python3
"""Shared workload manifest helpers for benchmark scripts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

預設略過工作負載 = {
    "example_clock": "需圖形/DOM 環境，非純 stdout。",
    "example_tree": "需圖形輸出，非純 stdout。",
    "example_tree2": "需圖形輸出，非純 stdout。",
}

預設工作負載清單檔 = Path("benchmark/workloads/MANIFEST")


@dataclass(frozen=True)
class 工作負載定義:
    """A benchmark workload entry parsed from manifest."""

    名稱: str
    路徑: str
    標籤: tuple[str, ...]
    規模: str
    套件: tuple[str, ...]
    配置: tuple[str, ...]
    說明: str


def 載入工作負載清單(
    路徑: Path,
) -> tuple[dict[str, 工作負載定義], dict[str, list[tuple[str, str]]]]:
    """Parse workload manifest and return workload definitions + groups."""

    內容 = 路徑.read_text(encoding="utf-8")
    區段: str | None = None
    群組名: str | None = None
    工作負載表: dict[str, 工作負載定義] = {}
    群組表: dict[str, list[tuple[str, str]]] = {}

    for 原行 in 內容.splitlines():
        行 = 原行.split("#", 1)[0].strip()
        if not 行:
            continue
        if 行.startswith("[") and 行.endswith("]"):
            名 = 行[1:-1].strip()
            if 名 == "workloads":
                區段 = "workloads"
                群組名 = None
            elif 名.startswith("group "):
                區段 = "group"
                群組名 = 名.split(" ", 1)[1].strip()
                if not 群組名:
                    raise ValueError(f"群組名不可為空：{原行}")
                群組表.setdefault(群組名, [])
            else:
                raise ValueError(f"未知區段：{名}")
            continue

        if 區段 == "workloads":
            if 行.startswith("name\t"):
                continue
            欄 = 行.split("\t")
            if len(欄) < 2:
                raise ValueError(f"workloads 行欄位不足：{原行}")
            名稱 = 欄[0].strip()
            檔路 = 欄[1].strip()
            標籤 = tuple(
                x
                for x in (欄[2].strip() if len(欄) >= 3 else "")
                .replace(",", " ")
                .split()
                if x
            )
            規模 = 欄[3].strip() if len(欄) >= 4 else ""
            套件 = tuple(
                x
                for x in (欄[4].strip() if len(欄) >= 5 else "")
                .replace(",", " ")
                .split()
                if x
            )
            配置 = tuple(
                x
                for x in (欄[5].strip() if len(欄) >= 6 else "")
                .replace(",", " ")
                .split()
                if x
            )
            說明 = 欄[6].strip() if len(欄) >= 7 else ""
            if not 名稱 or not 檔路:
                raise ValueError(f"workloads 行缺名稱或路徑：{原行}")
            if 名稱 in 工作負載表:
                raise ValueError(f"workload 重複：{名稱}")
            工作負載表[名稱] = 工作負載定義(名稱, 檔路, 標籤, 規模, 套件, 配置, 說明)
            continue

        if 區段 == "group":
            assert 群組名 is not None
            操作 = "+"
            目標 = 行
            if 行[0] in "+-":
                操作 = 行[0]
                目標 = 行[1:].strip()
            if not 目標:
                raise ValueError(f"group 行缺目標：{原行}")
            群組表[群組名].append((操作, 目標))
            continue

        raise ValueError(f"內容不在任何區段：{原行}")

    群組表.setdefault("all", [("+", "<all>")])
    群組表.setdefault("default", [("+", "<all>")])
    return 工作負載表, 群組表


def _解析選擇字串(文字: str) -> tuple[list[str], list[str]]:
    項列 = [x.strip() for x in 文字.split(",") if x.strip()]
    if not 項列 or 項列 == ["<default>"]:
        return ["default"], []
    正項: list[str] = []
    負項: list[str] = []
    for 項 in 項列:
        if 項.startswith("-"):
            名 = 項[1:].strip()
            if 名:
                負項.append(名)
        else:
            正項.append(項)
    if not 正項:
        正項 = ["all"]
    return 正項, 負項


def _解析群組(
    名稱: str,
    工作負載表: dict[str, 工作負載定義],
    群組表: dict[str, list[tuple[str, str]]],
    _路徑: tuple[str, ...] = (),
) -> list[str]:
    if 名稱 in _路徑:
        路 = " -> ".join(_路徑 + (名稱,))
        raise ValueError(f"群組循環：{路}")
    if 名稱 in {"<all>", "all"}:
        return list(工作負載表)
    if 名稱 in 工作負載表:
        return [名稱]
    if 名稱 not in 群組表:
        raise ValueError(f"未知 workload 或群組：{名稱}")

    結果: list[str] = []
    已有: set[str] = set()
    for 操作, 目標 in 群組表[名稱]:
        名列 = _解析群組(目標, 工作負載表, 群組表, _路徑 + (名稱,))
        if 操作 == "+":
            for 名 in 名列:
                if 名 not in 已有:
                    結果.append(名)
                    已有.add(名)
        elif 操作 == "-":
            排除 = set(名列)
            結果 = [名 for 名 in 結果 if 名 not in 排除]
            已有 = set(結果)
        else:
            raise ValueError(f"未知操作：{操作}")
    return 結果


def 選擇工作負載(
    文字: str,
    工作負載表: dict[str, 工作負載定義],
    群組表: dict[str, list[tuple[str, str]]],
    套件: str = "",
    配置: str = "",
    包含略過: bool = False,
) -> tuple[list[工作負載定義], list[str]]:
    """Resolve workload selection expression with suite/profile filters."""

    正項, 負項 = _解析選擇字串(文字)
    名單: list[str] = []
    已有: set[str] = set()
    for 項 in 正項:
        for 名 in _解析群組(項, 工作負載表, 群組表):
            if 名 not in 已有:
                名單.append(名)
                已有.add(名)

    排除: set[str] = set()
    for 項 in 負項:
        排除.update(_解析群組(項, 工作負載表, 群組表))

    略過說明: list[str] = []
    結果: list[工作負載定義] = []
    for 名 in 名單:
        if 名 in 排除:
            continue
        定義 = 工作負載表[名]
        if 套件 and 套件 not in 定義.套件:
            continue
        if 配置 and 配置 not in 定義.配置:
            continue
        原因 = 預設略過工作負載.get(定義.名稱)
        if 原因 and not 包含略過:
            略過說明.append(f"{定義.名稱}: {原因}")
            continue
        結果.append(定義)
    return 結果, 略過說明


def 載入工作負載源碼(
    工作目錄: Path,
    工作負載列: list[工作負載定義],
    基底目錄: Path | None = None,
) -> list[tuple[工作負載定義, str, str]]:
    """Load workload source files into memory."""

    結果: list[tuple[工作負載定義, str, str]] = []
    for 定義 in 工作負載列:
        路徑 = Path(定義.路徑).expanduser()
        if not 路徑.is_absolute():
            if 基底目錄 is not None:
                候選 = (基底目錄 / 路徑).resolve()
                if 候選.exists():
                    路徑 = 候選
                else:
                    路徑 = (工作目錄 / 路徑).resolve()
            else:
                路徑 = (工作目錄 / 路徑).resolve()
        內容 = 路徑.read_text(encoding="utf-8")
        結果.append((定義, str(路徑), 內容))
    return 結果
