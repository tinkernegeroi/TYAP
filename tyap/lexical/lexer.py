"""Лексер на основе предоставленного пользователем анализатора."""
from tyap.tokens import KEYWORDS, SYMBOLS, Token, TokenType, is_letter, is_word_char
from .models import LexerResult, LexicalError


class Lexer:
    def __init__(self, source: str):
        self.source = source.replace("\r\n", "\n").replace("\r", "\n")
        self.position = 0
        self.line = 1
        self.column = 1
        self.result = LexerResult()

    def _advance(self) -> None:
        char = self.source[self.position]
        self.position += 1
        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

    def _error(self, lexeme: str, line: int, column: int, message: str) -> None:
        self.result.errors.append(LexicalError(lexeme, line, column, message))
        self.result.tokens.append(Token(TokenType.INVALID, lexeme, line, column))

    def _scan_word(self) -> None:
        start = self.position
        line, column = self.line, self.column
        while self.position < len(self.source):
            if not is_word_char(self.source[self.position]):
                break
            self._advance()
        lexeme = self.source[start:self.position]

        if lexeme in KEYWORDS:
            token = Token(KEYWORDS[lexeme], lexeme, line, column)
        elif lexeme in ("0", "1"):
            index = self.result.constants.intern(lexeme)
            token = Token(TokenType.CONSTANT, lexeme, line, column, index)
        elif all(is_letter(char) for char in lexeme):
            index = self.result.identifiers.intern(lexeme)
            token = Token(TokenType.IDENTIFIER, lexeme, line, column, index)
        else:
            if lexeme[0].isdecimal():
                message = "Недопустимая константа: разрешены только отдельные 0 и 1"
            else:
                message = "Недопустимый идентификатор: разрешены только латинские буквы"
            self._error(lexeme, line, column, message)
            return
        self.result.tokens.append(token)

    def scan(self) -> LexerResult:
        self.position, self.line, self.column = 0, 1, 1
        self.result = LexerResult()
        while self.position < len(self.source):
            char = self.source[self.position]
            if char.isspace():
                self._advance()
            elif is_word_char(char):
                self._scan_word()
            elif char in SYMBOLS:
                self.result.tokens.append(
                    Token(SYMBOLS[char], char, self.line, self.column)
                )
                self._advance()
            else:
                self._error(char, self.line, self.column, "Неизвестный символ")
                self._advance()
        self.result.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.result
