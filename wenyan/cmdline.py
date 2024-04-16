import argparse
import ast
from pathlib import Path

from lark import Transformer, v_args

import wenyan

SHORT_SCALES = dict((s, 10 ** (i + 1)) for i, s in enumerate("十百千"))
LONG_SCALES = dict((s, 10 ** (i * 4 + 4)) for i, s in enumerate("萬億兆京垓秭穣溝澗正載極"))
DIGITS = dict((c, i) for i, c in enumerate("零一二三四五六七八九"))


def hanzi2num(hanzi):
    return DIGITS[hanzi]


@v_args(inline=True, meta=True)
class ToPyAST(Transformer):
    current_values: list[ast.Constant | ast.Name] = []

    # mod
    @v_args(inline=False, meta=False)
    def module(self, p):
        return ast.Module(body=p)

    # stmt
    def multiple_assign_stmt(self, meta, value, *targets):
        for target in targets:
            target.ctx = ast.Store()
        targets = [
            ast.Tuple(
                elts=list(targets),
                ctx=ast.Store(),
                lineno=meta.line,
                col_offset=meta.column,
            )
        ]
        return ast.Assign(
            targets=targets,
            value=value,
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )

    def expr_stmt(self, meta, value):
        return ast.Expr(
            value=value,
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )

    def for_in_range_stmt(self, meta, iterations, *body):
        body = list(body)
        target = ast.Name(
            id="_",
            ctx=ast.Store(),
            lineno=meta.line,
            col_offset=meta.column + 1,
            end_lineno=meta.line,
            end_col_offset=meta.column + 2,
        )
        iter_ = ast.Call(
            func=ast.Name(
                id="range",
                ctx=ast.Load(),
                lineno=meta.line,
                col_offset=meta.column + 1,
                end_lineno=iterations.end_lineno,
                end_col_offset=iterations.end_col_offset + 1,
            ),
            args=[iterations],
            keywords=[],
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )
        return ast.For(
            target=target,
            iter=iter_,
            body=body,
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )

    def print_stmt(self, meta):
        expr = ast.Expr(
            value=ast.Call(
                func=ast.Name(
                    id="print",
                    ctx=ast.Load(),
                    lineno=meta.line,
                    col_offset=meta.column,
                    end_lineno=meta.end_line,
                    end_col_offset=meta.end_column,
                ),
                args=self.current_values,
                keywords=[],
                lineno=meta.line,
                col_offset=meta.column,
            ),
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )
        self.current_values = []
        return expr

    # expr
    def multiple_declare_expr(self, meta, length, dtype, *elts):
        if len(elts) != length:
            raise ValueError(f"Expected {length} elements, got {len(elts)}")
        elts = list(elts)
        self.current_values = elts
        return ast.Tuple(
            elts=elts,
            ctx=ast.Load(),
            lineno=meta.line,
            col_offset=meta.column,
        )

    def constant_expr(self, meta, value):
        return ast.Constant(value=value, lineno=meta.line, col_offset=meta.column)

    def name_expr(self, meta, name):
        return ast.Name(
            id=name[1:-1],
            ctx=ast.Load(),
            lineno=meta.line,
            col_offset=meta.column,
            end_lineno=meta.end_line,
            end_col_offset=meta.end_column,
        )

    # builtin
    @v_args(inline=True, meta=False)
    def int(self, num):
        return hanzi2num(num)

    @v_args(inline=True, meta=False)
    def string(self, s):
        return s[2:-2]


def wenyan_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--version", action="version", version=wenyan.__version__)
    args = parser.parse_args()
    tree = wenyan.parser.parse(args.source.read_text())
    tree = ToPyAST().transform(tree)
    compiled = compile(tree, args.source, mode="exec")
    exec(compiled)
