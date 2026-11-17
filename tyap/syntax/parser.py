"""Детерминированный восходящий магазинный автомат SLR(1)."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tyap.diagnostics import ParseError
from tyap.grammar.rules import PRODUCTIONS
from tyap.grammar.table import build
from tyap.tokens import SYMBOLS, Token, TokenType
from .tree import Node

TERMINALS = {kind: spelling for spelling, kind in SYMBOLS.items()}
TERMINALS.update({TokenType.IDENTIFIER: 'ID', TokenType.CONSTANT: 'CONST'})


def terminal(token: Token) -> str:
    return TERMINALS.get(token.kind, token.kind.name)


@dataclass(frozen=True)
class TraceStep:
    states: tuple[int, ...]
    symbols: tuple[str, ...]
    position: int
    lookahead: Token
    action: str


class Parser:
    def __init__(self):
        # Строится из правил, а не из отдельной вручную синхронизируемой таблицы.
        self.action, self.goto, *_ = build()

    def parse(
        self, tokens: Sequence[Token], trace: Callable[[TraceStep], None] | None = None
    ) -> Node:
        """Принимает полный поток без INVALID, с единственным EOF в конце.

        При первой ошибке выбрасывает ParseError. Исправление входа и
        восстановление после ошибки намеренно не выполняются.
        """
        if not tokens or tokens[-1].kind != TokenType.EOF:
            raise ValueError('Поток должен завершаться EOF')
        if any(t.kind in (TokenType.INVALID, TokenType.EOF) for t in tokens[:-1]):
            raise ValueError('Поток содержит INVALID или преждевременный EOF')
        states = [0]
        nodes: list[Node] = []
        position = 0
        while True:
            token = tokens[position]
            symbol = terminal(token)
            row = self.action[states[-1]]
            action = row.get(symbol)
            if trace is not None:
                trace(TraceStep(tuple(states), tuple(n.symbol for n in nodes),
                                position, token, action or 'error'))
            if action is None:
                raise ParseError(token, tuple(sorted(row)))
            if action == 'ok':
                return nodes[0]
            number = int(action[1:])
            if action.startswith('s'):
                nodes.append(Node(symbol, token=token))
                states.append(number)
                position += 1
            else:
                left, right = PRODUCTIONS[number]
                size = len(right)
                children = tuple(nodes[-size:])
                del nodes[-size:]
                del states[-size:]
                nodes.append(Node(left, children, rule=number))
                states.append(self.goto[states[-1]][left])
