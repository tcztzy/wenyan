#!/usr/bin/env python3

import argparse
import ast
import csv
import html
import io
import tokenize
from pathlib import Path

欄位列 = (
    "輪次",
    "標籤",
    "行數",
    "位元組",
    "詞元",
    "AST節點",
    "AST分支",
    "AST最大深度",
    "Parser速度變化",
    "CompileAST速度變化",
    "幾何均值速度變化",
    "說明",
)

規模指標列 = (
    ("行數", "#0f766e"),
    ("位元組", "#1d4ed8"),
    ("詞元", "#7c3aed"),
    ("AST節點", "#c2410c"),
    ("AST分支", "#dc2626"),
    ("AST最大深度", "#0891b2"),
)

速度指標列 = (
    ("Parser速度變化", "#16a34a"),
    ("CompileAST速度變化", "#d97706"),
    ("幾何均值速度變化", "#0f172a"),
)

分支節點型別 = (
    ast.If,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.Try,
    ast.Match,
    ast.IfExp,
)


def _最大深度(節點: ast.AST, 深度: int = 0) -> int:
    子節點列 = list(ast.iter_child_nodes(節點))
    if not 子節點列:
        return 深度
    return max(_最大深度(子節點, 深度 + 1) for 子節點 in 子節點列)


def 計算Python檔指標(路徑: Path) -> dict[str, int]:
    原始 = 路徑.read_bytes()
    行數 = 原始.count(b"\n")

    with tokenize.open(路徑) as 句柄:
        源碼 = 句柄.read()

    詞元數 = sum(
        1
        for 詞元 in tokenize.generate_tokens(io.StringIO(源碼).readline)
        if 詞元.type
        not in {
            tokenize.ENCODING,
            tokenize.NL,
            tokenize.NEWLINE,
            tokenize.ENDMARKER,
        }
    )

    樹 = ast.parse(源碼, filename=str(路徑))
    AST節點數 = sum(1 for _ in ast.walk(樹))
    AST分支數 = sum(isinstance(節點, 分支節點型別) for 節點 in ast.walk(樹))

    return {
        "行數": 行數,
        "位元組": len(原始),
        "詞元": 詞元數,
        "AST節點": AST節點數,
        "AST分支": AST分支數,
        "AST最大深度": _最大深度(樹),
    }


def 讀取歷程(CSV路徑: Path) -> list[dict[str, str]]:
    if not CSV路徑.exists():
        return []
    with CSV路徑.open("r", encoding="utf-8", newline="") as 句柄:
        讀者 = csv.DictReader(句柄)
        return [{欄: 列.get(欄, "") for 欄 in 欄位列} for 列 in 讀者]


def 寫入歷程(CSV路徑: Path, 記錄列: list[dict[str, str]]) -> None:
    CSV路徑.parent.mkdir(parents=True, exist_ok=True)
    with CSV路徑.open("w", encoding="utf-8", newline="") as 句柄:
        寫手 = csv.DictWriter(句柄, 欄位列)
        寫手.writeheader()
        寫手.writerows(記錄列)


def 追加當前記錄(
    CSV路徑: Path,
    源碼路徑: Path,
    標籤: str | None = None,
    說明: str = "",
    Parser速度變化: float | None = None,
    CompileAST速度變化: float | None = None,
    幾何均值速度變化: float | None = None,
) -> dict[str, str]:
    記錄列 = 讀取歷程(CSV路徑)
    輪次 = len(記錄列)
    if 標籤 is None:
        標籤 = "起點" if 輪次 == 0 else f"第{輪次:02d}輪"
    指標 = 計算Python檔指標(源碼路徑)
    記錄 = {
        "輪次": str(輪次),
        "標籤": 標籤,
        "行數": str(指標["行數"]),
        "位元組": str(指標["位元組"]),
        "詞元": str(指標["詞元"]),
        "AST節點": str(指標["AST節點"]),
        "AST分支": str(指標["AST分支"]),
        "AST最大深度": str(指標["AST最大深度"]),
        "Parser速度變化": "" if Parser速度變化 is None else f"{Parser速度變化:.6f}",
        "CompileAST速度變化": ""
        if CompileAST速度變化 is None
        else f"{CompileAST速度變化:.6f}",
        "幾何均值速度變化": ""
        if 幾何均值速度變化 is None
        else f"{幾何均值速度變化:.6f}",
        "說明": 說明,
    }
    記錄列.append(記錄)
    寫入歷程(CSV路徑, 記錄列)
    return 記錄


def _折線點列(數列: list[float], 左: float, 上: float, 寬: float, 高: float) -> str:
    if len(數列) == 1:
        return f"{左 + 寬 / 2:.2f},{上 + 高 / 2:.2f}"
    最低 = min(數列)
    最高 = max(數列)
    if 最低 == 最高:
        最低 -= 1
        最高 += 1
    底 = 最低 - 2
    頂 = 最高 + 2
    點列: list[str] = []
    for 索引, 值 in enumerate(數列):
        X = 左 + 寬 * 索引 / (len(數列) - 1)
        Y = 上 + 高 * (頂 - 值) / (頂 - 底)
        點列.append(f"{X:.2f},{Y:.2f}")
    return " ".join(點列)


def _連續點段列(數列: list[float | None]) -> list[list[tuple[int, float]]]:
    段列: list[list[tuple[int, float]]] = []
    當前段: list[tuple[int, float]] = []
    for 索引, 值 in enumerate(數列):
        if 值 is None:
            if 當前段:
                段列.append(當前段)
                當前段 = []
            continue
        當前段.append((索引, 值))
    if 當前段:
        段列.append(當前段)
    return 段列


def 生成折線圖(記錄列: list[dict[str, str]], 標題: str = "Wenyan 簡化歷程") -> str:
    if not 記錄列:
        raise ValueError("無歷程可繪")

    寬 = 1200
    高 = 980
    左界 = 88
    上界 = 92
    圖寬 = 780
    上圖高 = 340
    下圖上界 = 534
    下圖高 = 220
    右欄X = 左界 + 圖寬 + 36
    上圖下界 = 上界 + 上圖高
    下圖下界 = 下圖上界 + 下圖高

    基準 = {欄: int(記錄列[0][欄]) or 1 for 欄, _ in 規模指標列}
    百分比列 = {
        欄: [100.0 * int(記錄[欄]) / 基準[欄] for 記錄 in 記錄列]
        for 欄, _ in 規模指標列
    }
    全值列 = [值 for 數列 in 百分比列.values() for 值 in 數列]
    最低 = min(全值列)
    最高 = max(全值列)
    底 = min(最低 - 2, 80.0)
    頂 = max(最高 + 2, 102.0)
    if 頂 - 底 < 12:
        底 -= 6
        頂 += 6

    def X(索引: int) -> float:
        if len(記錄列) == 1:
            return 左界 + 圖寬 / 2
        return 左界 + 圖寬 * 索引 / (len(記錄列) - 1)

    def 上圖Y(值: float) -> float:
        return 上界 + 上圖高 * (頂 - 值) / (頂 - 底)

    速度百分比列 = {
        欄: [
            100.0
            if 索引 == 0 and not 記錄.get(欄, "").strip()
            else (100.0 * float(記錄[欄]) if 記錄.get(欄, "").strip() else None)
            for 索引, 記錄 in enumerate(記錄列)
        ]
        for 欄, _ in 速度指標列
    }
    速度有效值列 = [100.0]
    for 數列 in 速度百分比列.values():
        速度有效值列.extend(值 for 值 in 數列 if 值 is not None)
    速度底 = min(min(速度有效值列) - 2, 96.0)
    速度頂 = max(max(速度有效值列) + 2, 104.0)
    if 速度頂 - 速度底 < 12:
        速度底 -= 6
        速度頂 += 6

    def 下圖Y(值: float) -> float:
        return 下圖上界 + 下圖高 * (速度頂 - 值) / (速度頂 - 速度底)

    線列: list[str] = []
    for 索引 in range(6):
        刻度值 = 底 + (頂 - 底) * 索引 / 5
        刻度Y = 上圖Y(刻度值)
        線列.append(
            f'<line x1="{左界}" y1="{刻度Y:.2f}" x2="{左界 + 圖寬}" '
            f'y2="{刻度Y:.2f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        線列.append(
            f'<text x="{左界 - 12}" y="{刻度Y + 4:.2f}" text-anchor="end" '
            f'font-size="12" fill="#475569">{刻度值:.1f}%</text>'
        )

    步長 = max(1, len(記錄列) // 10)
    for 索引, 記錄 in enumerate(記錄列):
        if 索引 % 步長 != 0 and 索引 != len(記錄列) - 1:
            continue
        刻度X = X(索引)
        線列.append(
            f'<line x1="{刻度X:.2f}" y1="{上界}" x2="{刻度X:.2f}" '
            f'y2="{上圖下界}" stroke="#f1f5f9" stroke-width="1" />'
        )
        線列.append(
            f'<line x1="{刻度X:.2f}" y1="{下圖上界}" x2="{刻度X:.2f}" '
            f'y2="{下圖下界}" stroke="#f1f5f9" stroke-width="1" />'
        )
        線列.append(
            f'<text x="{刻度X:.2f}" y="{下圖下界 + 24}" text-anchor="middle" '
            f'font-size="12" fill="#475569">{html.escape(記錄["輪次"])}</text>'
        )

    折線列: list[str] = []
    圖例列: list[str] = []
    for 索引, (欄, 顏色) in enumerate(規模指標列):
        點列 = " ".join(
            f"{X(位置):.2f},{上圖Y(值):.2f}" for 位置, 值 in enumerate(百分比列[欄])
        )
        折線列.append(
            f'<polyline fill="none" stroke="{顏色}" stroke-width="2.5" points="{點列}" />'
        )
        for 位置, 值 in enumerate(百分比列[欄]):
            折線列.append(
                f'<circle cx="{X(位置):.2f}" cy="{上圖Y(值):.2f}" r="2.8" fill="{顏色}" />'
            )
        最新 = 記錄列[-1][欄]
        圖例Y = 上界 + 18 + 索引 * 56
        圖例列.append(
            f'<line x1="{右欄X}" y1="{圖例Y}" x2="{右欄X + 26}" y2="{圖例Y}" '
            f'stroke="{顏色}" stroke-width="3" />'
        )
        圖例列.append(
            f'<text x="{右欄X + 36}" y="{圖例Y + 4}" font-size="15" fill="#0f172a">'
            f"{html.escape(欄)}</text>"
        )
        圖例列.append(
            f'<text x="{右欄X + 36}" y="{圖例Y + 24}" font-size="12" fill="#475569">'
            f'最新值: {html.escape(最新)}</text>'
        )
        圖例列.append(
            f'<text x="{右欄X + 36}" y="{圖例Y + 42}" font-size="12" fill="#475569">'
            f'相對起點: {百分比列[欄][-1]:.1f}%</text>'
        )

    速度圖例基準Y = 上界 + 18 + len(規模指標列) * 56 + 24
    圖例列.append(
        f'<text x="{右欄X}" y="{速度圖例基準Y}" font-size="15" fill="#0f172a" '
        'font-weight="700">速度變化</text>'
    )
    for 索引, (欄, 顏色) in enumerate(速度指標列):
        段列 = _連續點段列(速度百分比列[欄])
        for 段 in 段列:
            if len(段) >= 2:
                點列 = " ".join(f"{X(位置):.2f},{下圖Y(值):.2f}" for 位置, 值 in 段)
                折線列.append(
                    f'<polyline fill="none" stroke="{顏色}" stroke-width="2.5" points="{點列}" />'
                )
            for 位置, 值 in 段:
                折線列.append(
                    f'<circle cx="{X(位置):.2f}" cy="{下圖Y(值):.2f}" r="2.8" fill="{顏色}" />'
                )
        最新值 = next((值 for 值 in reversed(速度百分比列[欄]) if 值 is not None), None)
        圖例Y = 速度圖例基準Y + 18 + 索引 * 56
        圖例列.append(
            f'<line x1="{右欄X}" y1="{圖例Y}" x2="{右欄X + 26}" y2="{圖例Y}" '
            f'stroke="{顏色}" stroke-width="3" />'
        )
        圖例列.append(
            f'<text x="{右欄X + 36}" y="{圖例Y + 4}" font-size="15" fill="#0f172a">'
            f"{html.escape(欄)}</text>"
        )
        圖例列.append(
            f'<text x="{右欄X + 36}" y="{圖例Y + 24}" font-size="12" fill="#475569">'
            f'最新值: {"無" if 最新值 is None else f"{最新值:.1f}%"}'
            "</text>"
        )

    for 索引 in range(6):
        刻度值 = 速度底 + (速度頂 - 速度底) * 索引 / 5
        刻度Y = 下圖Y(刻度值)
        線列.append(
            f'<line x1="{左界}" y1="{刻度Y:.2f}" x2="{左界 + 圖寬}" '
            f'y2="{刻度Y:.2f}" stroke="#e5e7eb" stroke-width="1" />'
        )
        線列.append(
            f'<text x="{左界 - 12}" y="{刻度Y + 4:.2f}" text-anchor="end" '
            f'font-size="12" fill="#475569">{刻度值:.1f}%</text>'
        )

    說明 = "上圖相對第 0 輪；下圖相對前一輪（100%=持平，高於 100% 更快）。"
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{寬}" height="{高}" '
            'viewBox="0 0 1200 980">',
            '<rect width="100%" height="100%" fill="#ffffff" />',
            f'<text x="{左界}" y="40" font-size="28" fill="#0f172a" '
            f'font-weight="700">{html.escape(標題)}</text>',
            f'<text x="{左界}" y="62" font-size="14" fill="#475569">{html.escape(說明)}</text>',
            f'<text x="{左界}" y="{上界 - 18}" font-size="15" fill="#0f172a" font-weight="700">規模與結構</text>',
            f'<line x1="{左界}" y1="{上界}" x2="{左界}" y2="{上圖下界}" stroke="#94a3b8" stroke-width="1.5" />',
            f'<line x1="{左界}" y1="{上圖下界}" x2="{左界 + 圖寬}" y2="{上圖下界}" stroke="#94a3b8" stroke-width="1.5" />',
            f'<text x="{左界}" y="{下圖上界 - 18}" font-size="15" fill="#0f172a" font-weight="700">速度變化</text>',
            f'<line x1="{左界}" y1="{下圖上界}" x2="{左界}" y2="{下圖下界}" stroke="#94a3b8" stroke-width="1.5" />',
            f'<line x1="{左界}" y1="{下圖下界}" x2="{左界 + 圖寬}" y2="{下圖下界}" stroke="#94a3b8" stroke-width="1.5" />',
            *線列,
            *折線列,
            *圖例列,
            f'<text x="{左界 + 圖寬 / 2:.2f}" y="{高 - 28}" text-anchor="middle" '
            'font-size="13" fill="#475569">輪次</text>',
            '</svg>',
        ]
    )


def 寫出折線圖(
    CSV路徑: Path, SVG路徑: Path, 標題: str = "Wenyan 簡化歷程"
) -> None:
    記錄列 = 讀取歷程(CSV路徑)
    SVG路徑.parent.mkdir(parents=True, exist_ok=True)
    SVG路徑.write_text(生成折線圖(記錄列, 標題), encoding="utf-8")


def main() -> int:
    解析器 = argparse.ArgumentParser(description="維護 Wenyan 簡化歷程 CSV 與 SVG。")
    子命令 = 解析器.add_subparsers(dest="命令", required=True)

    追加器 = 子命令.add_parser("append", help="追加當前 wenyan.py 指標並重畫折線圖")
    追加器.add_argument("csv_path")
    追加器.add_argument("svg_path")
    追加器.add_argument("--source", default="wenyan.py")
    追加器.add_argument("--label")
    追加器.add_argument("--note", default="")
    追加器.add_argument("--parser-speed", type=float)
    追加器.add_argument("--compile-ast-speed", type=float)
    追加器.add_argument("--geomean-speed", type=float)
    追加器.add_argument("--title", default="Wenyan 簡化歷程")

    繪製器 = 子命令.add_parser("render", help="依既有 CSV 重畫折線圖")
    繪製器.add_argument("csv_path")
    繪製器.add_argument("svg_path")
    繪製器.add_argument("--title", default="Wenyan 簡化歷程")

    參數 = 解析器.parse_args()
    if 參數.命令 == "append":
        CSV路徑 = Path(參數.csv_path)
        SVG路徑 = Path(參數.svg_path)
        追加當前記錄(
            CSV路徑,
            Path(參數.source),
            標籤=參數.label,
            說明=參數.note,
            Parser速度變化=參數.parser_speed,
            CompileAST速度變化=參數.compile_ast_speed,
            幾何均值速度變化=參數.geomean_speed,
        )
        寫出折線圖(CSV路徑, SVG路徑, 參數.title)
        return 0

    寫出折線圖(Path(參數.csv_path), Path(參數.svg_path), 參數.title)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
