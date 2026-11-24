"""Исполнение абстрактного синтаксического дерева языка TYAP."""
from collections import deque
from typing import TextIO

from tyap.diagnostics import ExecutionError
from tyap.semantic import validate
from tyap.syntax.tree import Node


def evaluate(expression: Node, variables: dict[str, bool]) -> bool:
    """Вычисляет операнды слева направо без рекурсии по глубине выражения."""
    pending: list[Node | str] = [expression]
    values: list[bool] = []
    while pending:
        item = pending.pop()
        if isinstance(item, Node):
            if item.symbol == 'ID':
                values.append(variables[item.token.lexeme])
            elif item.symbol in ('0', '1'):
                values.append(item.symbol == '1')
            else:
                pending.append(item.symbol)
                pending.extend(reversed(item.children))
        elif item == 'Unary NOT':
            values.append(not values.pop())
        else:
            right = values.pop()
            left = values.pop()
            match item:
                case 'Binary AND':
                    values.append(left and right)
                case 'Binary OR':
                    values.append(left or right)
                case 'Binary IMP':
                    values.append(not left or right)
                case _:
                    raise ValueError(f'Неизвестная операция AST: {item}')
    return values.pop()


class Interpreter:
    def __init__(self, input_stream: TextIO, output_stream: TextIO, *, prompts: TextIO | None = None):
        self.input = input_stream
        self.output = output_stream
        self.prompts = prompts
        self.buffer: deque[str] = deque()

    def run(self, program: Node) -> None:
        validate(program)
        variables: dict[str, bool] = {}
        block, _ = program.children
        for statement in block.children:
            match statement.symbol:
                case 'Assignment':
                    self._assign(statement, variables)
                case 'READ':
                    for identifier in statement.children:
                        variables[identifier.token.lexeme] = self._read(identifier)
                case 'WRITE':
                    print(*(int(variables[id_node.token.lexeme]) for id_node in statement.children),
                          file=self.output)
                case 'REPEAT':
                    self._repeat(statement, variables)
                case _:
                    raise ValueError(f'Неизвестная команда AST: {statement.symbol}')

    @staticmethod
    def _assign(statement: Node, variables: dict[str, bool]) -> None:
        target, expression = statement.children
        variables[target.token.lexeme] = evaluate(expression, variables)

    def _read(self, identifier: Node) -> bool:
        token = identifier.token
        while not self.buffer:
            if self.prompts is not None:
                print(f'{token.lexeme} (0 или 1): ', end='', file=self.prompts, flush=True)
            line = self.input.readline()
            if not line:
                raise ExecutionError(token, f'Ввод закончился до чтения {token.lexeme!r}')
            self.buffer.extend(line.split())
        value = self.buffer.popleft()
        if value not in ('0', '1'):
            raise ExecutionError(token, f'Для {token.lexeme!r} ожидалось 0 или 1, получено {value!r}')
        return value == '1'

    def _repeat(self, statement: Node, variables: dict[str, bool]) -> None:
        body, condition = statement.children
        # Только цели присваиваний могут изменяться между итерациями.
        targets = tuple(dict.fromkeys(s.children[0].token.lexeme for s in body.children))
        seen: set[tuple[bool, ...]] = set()
        while True:
            for assignment in body.children:
                self._assign(assignment, variables)
            if evaluate(condition, variables):
                return
            state = tuple(variables[name] for name in targets)
            if state in seen:
                token = body.children[0].children[0].token
                raise ExecutionError(token, 'Цикл REPEAT повторяет состояние при ложном UNTIL')
            seen.add(state)
