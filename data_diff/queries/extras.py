"Useful AST classes that don't quite fall within the scope of regular SQL"

from typing import Callable, Sequence
from runtype import dataclass

from data_diff.databases.database_types import ColType, Native_UUID

from .compiler import Compiler
from .ast_classes import Expr, ExprNode, Concat


@dataclass
class NormalizeAsString(ExprNode):
    expr: ExprNode
    type: ColType = None

    def compile(self, c: Compiler) -> str:
        expr = c.compile(self.expr)
        return c.database.normalize_value_by_type(expr, self.type or self.expr.type)


@dataclass
class ApplyFuncAndNormalizeAsString(ExprNode):
    expr: ExprNode
    apply_func: Callable = None

    def compile(self, c: Compiler) -> str:
        expr = self.expr
        expr_type = expr.type

        if isinstance(expr_type, Native_UUID):
            # Normalize first, apply template after (for uuids)
            # Needed because min/max(uuid) fails in postgresql
            expr = NormalizeAsString(expr, expr_type)
            if self.apply_func is not None:
                expr = self.apply_func(expr)  # Apply template using Python's string formatting

        else:
            # Apply template before normalizing (for ints)
            if self.apply_func is not None:
                expr = self.apply_func(expr)  # Apply template using Python's string formatting
            expr = NormalizeAsString(expr, expr_type)

        return c.compile(expr)


@dataclass
class Checksum(ExprNode):
    exprs: Sequence[Expr]

    def compile(self, c: Compiler):
        if len(self.exprs) > 1:
            exprs = [f"coalesce({c.compile(expr)}, '<null>')" for expr in self.exprs]
            # exprs = [c.compile(e) for e in exprs]
            expr = Concat(exprs, "|")
        else:
            # No need to coalesce - safe to assume that key cannot be null
            (expr,) = self.exprs
        expr = c.compile(expr)
        md5 = c.database.md5_to_int(expr)
        return f"sum({md5})"
