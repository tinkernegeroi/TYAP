"""Диагностика с координатами в исходной программе."""
from tyap.tokens import Token


class ParseError(Exception):
    def __init__(self, token: Token, expected: tuple[str, ...]):
        self.token = token
        self.expected = expected
        actual = repr(token.lexeme) if token.lexeme else 'конец файла'
        super().__init__(
            f'Строка {token.line}, столбец {token.column}: '
            f'неожиданный {actual}; ожидалось: {", ".join(expected)}'
        )


class SemanticError(Exception):
    def __init__(self, token: Token, message: str):
        super().__init__(f'Семантическая ошибка. Строка {token.line}, столбец {token.column}: {message}')


class ExecutionError(Exception):
    def __init__(self, token: Token, message: str):
        super().__init__(f'Ошибка выполнения. Строка {token.line}, столбец {token.column}: {message}')
