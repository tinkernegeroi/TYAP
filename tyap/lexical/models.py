"""Результат сканирования и таблицы символов."""
from dataclasses import dataclass, field
from tyap.tokens import Token

@dataclass(frozen=True)
class LexicalError:
    lexeme: str
    line: int
    column: int
    message: str

    def __str__(self) -> str:
        return (
            f"Строка {self.line}, столбец {self.column}: "
            f"{self.message} ({self.lexeme!r})"
        )


@dataclass
class SymbolTable:
    """Список хранит элементы, словарь ускоряет поиск их индексов."""

    entries: list[str] = field(default_factory=list)
    _indices: dict[str, int] = field(default_factory=dict, repr=False)

    def intern(self, lexeme: str) -> int:
        if lexeme not in self._indices:
            self._indices[lexeme] = len(self.entries)
            self.entries.append(lexeme)
        return self._indices[lexeme]


@dataclass
class LexerResult:
    tokens: list[Token] = field(default_factory=list)
    identifiers: SymbolTable = field(default_factory=SymbolTable)
    constants: SymbolTable = field(default_factory=SymbolTable)
    errors: list[LexicalError] = field(default_factory=list)


