# AGENTS.md

## 项目概览
- Wenyan（文言）编程语言的 Python 实现。
- 主要入口与发布载体：`wenyan.py`（本项目倾向保持核心实现集中，便于分发与自举）。
- 行为规范参考：`SPEC.md`（描述 *实际* lexer/token 行为），以及 `wy.spec`（语法文件，若涉及语法变更需同步更新）。

## 核心原则（必须遵守）
- **Python 3.8+ 兼容**：所有代码必须在 Python 3.8 及以上版本 *可解析并可运行*（以 tox 的 `py38` 为底线）。
  - 允许使用较新的 *类型注解写法*（例如 PEP 604 `A | B`、PEP 585 `list[str]`），但必须确保在 Python 3.8 下不会因为“运行时求值注解”而报错：统一启用 `from __future__ import annotations`，且避免在运行时解析注解（如 `typing.get_type_hints()`）或依赖注解做逻辑判断。
  - 禁止使用确实属于新语法且 Python 3.8 无法解析的特性（例如结构化模式匹配 `match/case`、`except*` 等）。
- **内部标识符用繁体中文**：核心实现与测试中的内部变量/函数/类/常量，优先使用繁体中文命名（自举需要，且与 Wenyan 语境一致）。
  - 允许的例外：Python 约定的 dunder（如 `__all__`）、第三方库/标准库 API 名称、以及与 CLI/生态对接不可避免的英文标识（如 `argv`、`Path`）。
  - AST/IR 的「節點類名」与字段名应尽量采用文言/繁体中文（优先使用语言自身术语与关键字），以降低未来自举迁移成本。
- **覆盖率 100%（严格）**：本项目属于编程语言实现，质量门槛高；测试覆盖率以 *行覆盖率* 为准，目标必须达到 **100%**。
  - 说明：覆盖率不可能“超过 100%”，因此“100% 以上”在此等价为“必须达到 100% 且不得通过大面积排除来规避”。若确需排除（极少数），必须在变更说明中写清原因与替代保障。
- **性能优先**：词法/解析等热路径要关注算法复杂度与分配次数；避免不必要的中间字符串、正则滥用与多次遍历。
- **零第三方依赖（运行时）**：不得引入任何第三方库作为运行时依赖（自举约束）；`pyproject.toml` 的 `[project] dependencies` 必须保持为空。
  - **标准库也要少用**：新增 `import` 视为依赖成本；优先使用最基础的内建数据结构/字符串处理；确需新增标准库模块时，必须在变更说明中写清理由与替代方案。
  - **开发工具与运行时隔离**：uv/tox/ruff/mypy/pre-commit 等仅用于开发；不得让最终用户运行/导入时依赖这些工具。
- **最小改动**：修改尽量小而可验证，避免过度抽象。

## 环境与常用命令
- 依赖与虚拟环境（uv）：
  - `uv sync`
  - 原则上不新增运行时依赖；如需新增/移除开发依赖：`uv add --dev <package>` / `uv remove --dev <package>`
- 单元测试（unittest）：
  - `uv run python -m unittest discover -s tests -p "test_*.py"`
- 测试矩阵（tox，见 `pyproject.toml` 的 `[tool.tox]`）：
  - `uv run tox`
- 代码风格（pre-commit / ruff）：
  - `uv run pre-commit run -a`（如已安装 pre-commit）
  - `uv run ruff check --fix .`
  - `uv run ruff format .`

## 静态检查与类型
- 以 pre-commit 中的检查为准（当前包含 ruff/ruff-format/mypy）。
  - 可运行：`uv run pre-commit run -a` 或 `uv run pre-commit run mypy -a`（如已安装 pre-commit）。
- 类型检查（可选，若已安装 ty）：`uv run ty check`。
- 若使用类型忽略，需对应工具标注且尽量最小化：
  - mypy：`# type: ignore[code]`
  - ty：`# ty:ignore[code]`

## 代码规范
- **命名**：
  - 内部命名使用繁体中文；同一概念在全仓库保持一致译名/写法（例如「詞法」「文法」「符號」「位置」等）。
  - 对外（CLI/README/异常信息）可使用更易懂的中文表述，但要保持术语一致，避免同一概念多套叫法。
- **类型标注**：
  - 以 Python 3.8 为底线：禁止使用 Python 3.8 无法解析的新语法（如 `match/case`、`except*` 等）。
  - 类型注解可使用较新写法（如 `A | B`、`list[str]`），但必须保持“仅用于静态分析”：推荐在所有模块启用 `from __future__ import annotations`，并避免在运行时解析/求值注解。
  - 如需最大兼容/最小惊喜，也可继续使用 `typing` 中的 `Optional/Union/List/Dict/...` 写法（两种风格择一并在同一文件内保持一致）。
- **文档与注释**：
  - Docstring 必须遵循 Google 风格；说明 *输入/输出/异常/边界条件*。
  - 若某模块已采用 doctest 风格示例，则新增示例沿用 doctest；否则优先新增 `unittest` 测试。
- **错误处理**：
  - 语法/词法相关错误统一使用 `文法之禍`（或其别名）并尽量携带可定位信息（例如 `slice(start, end)`）。
  - 错误信息尽量稳定（测试/用户会依赖），变更需同步更新测试与说明。
- **文件与编码**：
  - 源码一律 UTF-8；保持无多余尾随空白与一致的换行（pre-commit 会检查）。

## 测试与质量控制
- **新增/修复必须带测试**：任何行为改动都要有对应测试覆盖（含错误路径与边界情况）。
- **示例即回归**：`tests/test_examples.py` 会跑 `examples/*.wy`；新增语法/特性时应补充示例并保证可稳定执行。
- **覆盖率执行方式（零新增依赖，建议）**：
  - 使用标准库 `trace` 统计行覆盖：`python -m trace --count --summary -m unittest ...`（如需门禁，可写小脚本解析统计结果）。

## 变更同步要求
- 改动 lexer/token 行为：必须更新 `SPEC.md`（描述“实际行为”）并补齐测试。
- 改动语法/关键字/语义：更新 `wy.spec`、示例程序与测试；必要时更新版本号与发布说明。
