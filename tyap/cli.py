"""Консольный интерфейс без логики распознавания."""
import argparse
from contextlib import nullcontext
from pathlib import Path
import sys

from tyap.diagnostics import ExecutionError, ParseError, SemanticError
from tyap.interpreter import Interpreter
from tyap.lexical.lexer import Lexer
from tyap.syntax.nodes import build_ast
from tyap.syntax.parser import Parser, TraceStep

DEMO = Path(__file__).resolve().parents[1] / 'examples/valid/program.tyap'


def print_trace(step: TraceStep) -> None:
    print(f'{step.position:>4} | {" ".join(map(str, step.states))} | '
          f'{" ".join(step.symbols)} | {step.lookahead.lexeme or "EOF"} | {step.action}')


def main(argv: list[str] | None = None) -> int:
    arguments = argparse.ArgumentParser(description='TYAP — анализатор языка варианта 10')
    arguments.add_argument('file', nargs='?', help='Файл UTF-8; - для stdin; без аргумента — пример')
    arguments.add_argument('--tokens', action='store_true', help='Лексемы и таблицы символов')
    arguments.add_argument('--trace', action='store_true', help='Показать переносы и свёртки')
    arguments.add_argument('--tree', action='store_true', help='Показать дерево разбора')
    arguments.add_argument('--tree-output', type=Path, help='Сохранить дерево в текстовый файл UTF-8')
    arguments.add_argument('--run', action='store_true', help='Выполнить программу после разбора')
    arguments.add_argument('--input', type=Path, metavar='FILE', help='Прочитать данные READ из файла UTF-8')
    args = arguments.parse_args(argv)
    if args.input and not args.run:
        arguments.error('--input используется вместе с --run')
    try:
        source = sys.stdin.read() if args.file == '-' else Path(args.file or DEMO).read_text(encoding='utf-8-sig')
        result = Lexer(source).scan()
        if args.tokens:
            print('Код  Вид           Лексема          Строка:столбец  Индекс')
            for token in result.tokens:
                print(f'{token.code:<4} {token.kind.name:<13} {token.lexeme!r:<16} '
                      f'{token.line}:{token.column}  {token.symbol_index}')
            print('Идентификаторы:', list(enumerate(result.identifiers.entries)))
            print('Константы:', list(enumerate(result.constants.entries)))
        if result.errors:
            for error in result.errors:
                print(f'Лексическая ошибка. {error}', file=sys.stderr)
            return 1
        if args.trace:
            print('Вход | Стек состояний | Стек символов | Следующая лексема | Действие')
        tree = Parser().parse(result.tokens, print_trace if args.trace else None)
        if args.tree or args.tree_output or args.run:
            tree = build_ast(tree)
        if args.tree:
            for line in tree.lines():
                print(line)
        if args.tree_output:
            with args.tree_output.open('w', encoding='utf-8') as output:
                for line in tree.lines():
                    output.write(line + '\n')
        if args.run:
            data = args.input.open(encoding='utf-8-sig') if args.input else nullcontext(sys.stdin)
            with data as stream:
                prompts = sys.stderr if stream is sys.stdin and stream.isatty() else None
                Interpreter(stream, sys.stdout, prompts=prompts).run(tree)
        else:
            print('Синтаксический анализ успешно завершён.')
        return 0
    except ParseError as error:
        print(f'Синтаксическая ошибка. {error}', file=sys.stderr)
        return 1
    except (SemanticError, ExecutionError) as error:
        print(error, file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as error:
        print(f'Ошибка чтения или записи файла: {error}', file=sys.stderr)
        return 2
