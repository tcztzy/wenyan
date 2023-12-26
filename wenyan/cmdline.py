import argparse
import ast
from pathlib import Path

from lark import Transformer, v_args

import wenyan


Chinese_digits = dict((c, i) for i, c in enumerate("零一二三四五六七八九"))


def hanzi2num(hanzi):
    return Chinese_digits[hanzi]


class ToPyAST(Transformer):
    current_value = ast.Constant(value=None)

    def program(self, p):
        return ast.Module(body=p)

    @v_args(inline=True)
    def data(self, data):
        return data

    @v_args(inline=True, meta=True)
    def STRING_LITERAL(self, meta):
        return ast.Constant(
            value=str(meta[2:-2]), lineno=meta.line, col_offset=meta.column
        )

    @v_args(inline=True, meta=True)
    def statement(self, meta, s):
        return ast.Expr(value=s, lineno=meta.line, col_offset=meta.column)

    @v_args(inline=True, meta=True)
    def declare_statement(self, meta, num, dtype, *data):
        num = hanzi2num(str(num))
        if num < 0:
            raise
        if num == 1:
            self.current_value = data[0]
        else:
            self.current_value = ast.Tuple(
                elts=list(data),
                ctx=ast.Load(),
                lineno=meta.line,
                col_offset=meta.column,
            )
        return self.current_value

    @v_args(inline=True, meta=True)
    def print_statement(self, meta):
        if isinstance(self.current_value, ast.Constant):
            args = [self.current_value]
        else:
            args = [
                ast.Starred(
                    value=self.current_value,
                    ctx=ast.Load(),
                    lineno=meta.line,
                    col_offset=meta.column,
                )
            ]
        return ast.Call(
            func=ast.Name(
                id="print", ctx=ast.Load(), lineno=meta.line, col_offset=meta.column
            ),
            args=args,
            lineno=meta.line,
            col_offset=meta.column,
        )


def wenyan_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--version", action="version", version=wenyan.__version__)
    args = parser.parse_args()
    tree = wenyan.parser.parse(args.source.read_text())
    tree = ToPyAST().transform(tree)
    compiled = compile(tree, args.source, mode="exec")
    exec(compiled)
