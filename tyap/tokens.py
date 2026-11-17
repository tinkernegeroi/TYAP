"""Типы лексем и фиксированные коды исходного лексера."""
from dataclasses import dataclass
from enum import IntEnum


class TokenType(IntEnum):
    """Фиксированные числовые коды видов лексем."""

    EOF = 0
    BEGIN = 1
    END = 2
    VAR = 3
    LOGICAL = 4
    NOT = 5
    AND = 6
    OR = 7
    IMP = 8
    READ = 9
    REPEAT = 10
    WRITE = 11
    UNTIL = 12
    SEMICOLON = 20
    ASSIGN = 21
    LPAREN = 22
    RPAREN = 23
    COMMA = 24
    COLON = 25
    IDENTIFIER = 100
    CONSTANT = 101
    INVALID = 255


KEYWORDS = {
    name: TokenType[name]
    for name in (
        "BEGIN", "END", "VAR", "LOGICAL", "NOT", "AND", "OR", "IMP",
        "READ", "REPEAT", "WRITE", "UNTIL",
    )
}

SYMBOLS = {
    ";": TokenType.SEMICOLON,
    "=": TokenType.ASSIGN,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    ",": TokenType.COMMA,
    ":": TokenType.COLON,
}


def is_letter(char: str) -> bool:
    return "A" <= char <= "Z" or "a" <= char <= "z"


def is_word_char(char: str) -> bool:
    return char.isalnum() or char == "_"


@dataclass(frozen=True)
class Token:
    kind: TokenType
    lexeme: str
    line: int
    column: int
    symbol_index: int | None = None

    @property
    def code(self) -> int:
        return int(self.kind)

    @property
    def pair(self) -> tuple[int, int | None]:
        return self.code, self.symbol_index
