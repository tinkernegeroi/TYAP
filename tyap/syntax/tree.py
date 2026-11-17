"""Конкретное дерево разбора: сохраняет правила, лексемы и координаты."""
from dataclasses import dataclass
from tyap.tokens import Token


@dataclass(frozen=True)
class Node:
    symbol: str
    children: tuple['Node', ...] = ()
    token: Token | None = None
    rule: int | None = None

    def lines(self):
        """Итеративный обход не ограничивает глубину дерева рекурсией Python."""
        pending = [(self, 0)]
        while pending:
            node, depth = pending.pop()
            label = node.symbol
            if node.token:
                label += f' {node.token.lexeme!r} [{node.token.line}:{node.token.column}]'
            elif node.rule is not None:
                label += f' (r{node.rule})'
            yield '  ' * depth + label
            pending.extend((child, depth + 1) for child in reversed(node.children))
