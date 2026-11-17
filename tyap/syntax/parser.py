"""Восходящий магазинный автомат варианта 10."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from tyap.diagnostics import ParseError
from tyap.grammar.rules import BINARY_PRIORITY, PRODUCTIONS
from tyap.grammar.table import build
from tyap.tokens import SYMBOLS, Token, TokenType
from .tree import Node

TERMINALS = {kind: spelling for spelling, kind in SYMBOLS.items()}
TERMINALS[TokenType.IDENTIFIER] = 'ID'


def terminal(token: Token) -> str:
    if token.kind == TokenType.CONSTANT:
        return token.lexeme
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
            if action is not None and '/' in action:
                action = self._choose_action(action, nodes[-2], symbol)
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
                self._reduce(number, states, nodes)

    @staticmethod
    def _choose_action(actions: str, operator: Node, lookahead: str) -> str:
        reduce, shift = actions.split('/')
        previous = operator.children[0].symbol
        return shift if BINARY_PRIORITY[lookahead] > BINARY_PRIORITY[previous] else reduce

    def _reduce(self, number: int, states: list[int], nodes: list[Node]) -> None:
        left, right = PRODUCTIONS[number]
        size = len(right)
        children = tuple(nodes[-size:])
        del nodes[-size:]
        del states[-size:]
        nodes.append(Node(left, children, rule=number))
        states.append(self.goto[states[-1]][left])
