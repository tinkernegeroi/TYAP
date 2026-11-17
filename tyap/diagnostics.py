"""Ошибки синтаксического этапа."""
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
