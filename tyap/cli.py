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


def read_console_source() -> str | None:
    print('Введите программу. Завершите ввод точкой на отдельной строке.\n'
          'Чтобы запустить пример, нажмите Enter в первой строке.', flush=True)
    lines = []
    for line in sys.stdin:
        if not lines and not line.strip():
            return None
        if line.strip() == '.':
            break
        lines.append(line)
    return ''.join(lines)


def main(argv: list[str] | None = None) -> int:
    arguments = argparse.ArgumentParser(description='TYAP — анализатор языка варианта 10')
    sources = arguments.add_mutually_exclusive_group()
    sources.add_argument('file', nargs='?', help='Проверить файл UTF-8 или - для stdin')
    sources.add_argument('--file', dest='run_file', type=Path, metavar='ПУТЬ',
                         help='Показать и выполнить программу из файла UTF-8')
    sources.add_argument('--console', action='store_true',
                         help='Ввести и выполнить программу в консоли (по умолчанию при запуске без параметров)')
    arguments.add_argument('--tokens', action='store_true', help='Лексемы и таблицы символов')
    arguments.add_argument('--trace', action='store_true', help='Показать переносы и свёртки')
    arguments.add_argument('--tree', action='store_true', help='Показать дерево разбора')
    arguments.add_argument('--tree-output', type=Path, help='Сохранить дерево в текстовый файл UTF-8')
    arguments.add_argument('--run', action='store_true', help='Выполнить программу после разбора')
    arguments.add_argument('--input', type=Path, metavar='FILE', help='Прочитать данные READ из файла UTF-8')
    argv = sys.argv[1:] if argv is None else argv
    args = arguments.parse_args(argv)
    console = args.console or not argv
    execute = console or args.run_file is not None or args.run
    if args.input and not execute:
        arguments.error('--input используется вместе с --run, --file или --console')
    try:
        source = read_console_source() if console else None
        if args.file == '-':
            source = sys.stdin.read()
            if not sys.stdin.isatty():
                print(source, end='' if source.endswith('\n') else '\n', flush=True)
        elif source is None:
            path = Path(args.run_file or args.file or DEMO)
            source = path.read_text(encoding='utf-8-sig')
            print(f'Программа из файла {path}:')
            print(source, end='' if source.endswith('\n') else '\n', flush=True)
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
        if args.tree or args.tree_output or execute:
            tree = build_ast(tree)
        if args.tree:
            for line in tree.lines():
                print(line)
        if args.tree_output:
            with args.tree_output.open('w', encoding='utf-8') as output:
                for line in tree.lines():
                    output.write(line + '\n')
        if execute:
            data = args.input.open(encoding='utf-8-sig') if args.input else nullcontext(sys.stdin)
            with data as stream:
                prompts = sys.stderr if stream is sys.stdin and (stream.isatty() or console) else None
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
