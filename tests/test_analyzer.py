import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tyap.cli import main
from tyap.diagnostics import ParseError
from tyap.grammar.rules import PRODUCTIONS
from tyap.grammar.table import build
from tyap.lexical.lexer import Lexer
from tyap.syntax.parser import Parser
from tyap.tokens import TokenType

ROOT = Path(__file__).resolve().parents[1]


def program(commands='A = 1;'):
    return f'VAR A,B,C,D:LOGICAL;\nBEGIN\n{commands}\nEND'


def parse(source):
    result = Lexer(source).scan()
    if result.errors:
        raise AssertionError(result.errors)
    return Parser().parse(result.tokens)


def expression(node):
    """Независимая нормализация дерева для проверки группировки операций."""
    if node.token:
        return node.token.lexeme
    children = node.children
    if len(children) == 1:
        return expression(children[0])
    if len(children) == 2:
        return (expression(children[0]), expression(children[1]))
    if children[0].symbol == '(':
        return expression(children[1])
    return (expression(children[1]), expression(children[0]), expression(children[2]))


def assignment_expression(tree):
    pending = [tree]
    while pending:
        node = pending.pop()
        if node.symbol == 'Assignment':
            return expression(node.children[2])
        pending.extend(reversed(node.children))
    raise AssertionError('Assignment missing')


class LexerTests(unittest.TestCase):
    def test_original_codes_and_symbol_indices(self):
        result = Lexer('A A B 0 1 0').scan()
        self.assertEqual(result.identifiers.entries, ['A', 'B'])
        self.assertEqual(result.constants.entries, ['0', '1'])
        self.assertEqual([t.pair for t in result.tokens],
                         [(100, 0), (100, 0), (100, 1), (101, 0), (101, 1), (101, 0), (0, None)])

    def test_invalid_words_are_not_split(self):
        for word in ['1D', 'B1', '2', '10', 'A_B', 'А', 'lower', 'ABCDEFGHI']:
            with self.subTest(word=word):
                result = Lexer(word).scan()
                self.assertEqual(len(result.errors), 1)
                self.assertEqual(result.tokens[0].lexeme, word)
                self.assertEqual(result.tokens[0].kind, TokenType.INVALID)
        self.assertFalse(Lexer('ABCDEFGH').scan().errors)

    def test_operators(self):
        self.assertFalse(Lexer('A.AND.B.OR..NOT.C.IMP.1').scan().errors)
        for word in ['AND', 'NOT', 'OR', 'IMP', '.AND', '.X.', '.and.']:
            with self.subTest(word=word):
                self.assertTrue(Lexer(word).scan().errors)

    def test_positions_and_repeat_scan(self):
        lexer = Lexer('A\r\n  B\rC')
        first = lexer.scan()
        self.assertEqual([(t.line, t.column) for t in first.tokens], [(1, 1), (2, 3), (3, 1), (3, 2)])
        self.assertEqual(first, lexer.scan())


class ParserTests(unittest.TestCase):
    def test_valid_examples(self):
        for path in (ROOT / 'examples/valid').glob('*.tyap'):
            with self.subTest(path=path.name):
                self.assertEqual(parse(path.read_text(encoding='utf-8')).symbol, 'Program')

    def test_commands(self):
        for commands in ['A=0;', 'READ(A,B);', 'WRITE(A);',
                         'REPEAT A=1; B=.NOT.A; UNTIL (A.OR.B);',
                         'A=.NOT..NOT.1;', 'A=(1);', 'A=1; B=0; WRITE(A,B);']:
            with self.subTest(commands=commands):
                parse(program(commands))

    def test_invalid_syntax(self):
        invalid = ['', 'BEGIN A=1; END VAR A:LOGICAL',
                   'VAR A:LOGICAL BEGIN A=1; END',
                   'VAR :LOGICAL; BEGIN A=1; END', program('')]
        invalid += [program(body) for body in [
            'A=1', 'READ();', 'WRITE(A,);', 'A=;', 'A=(1;', 'A=1);',
            'A=1.AND.;', 'REPEAT UNTIL A;', 'REPEAT A=1; UNTIL ;',
            'REPEAT READ(A); UNTIL A;', 'REPEAT REPEAT A=1; UNTIL A; UNTIL A;',
            'REPEAT A=1; UNTIL A', 'A=1;;']]
        invalid += [program() + ' A', program()[:-3]]
        for source in invalid:
            with self.subTest(source=source), self.assertRaises(ParseError):
                parse(source)

    def test_precedence_and_associativity(self):
        cases = {
            '.NOT.A.AND.B.OR.C.IMP.D': ('.IMP.', ('.OR.', ('.AND.', ('.NOT.', 'A'), 'B'), 'C'), 'D'),
            'A.IMP.B.IMP.C': ('.IMP.', ('.IMP.', 'A', 'B'), 'C'),
            'A.OR.B.AND.C': ('.OR.', 'A', ('.AND.', 'B', 'C')),
            '.NOT.(A.OR.B)': ('.NOT.', ('.OR.', 'A', 'B')),
        }
        for source, expected in cases.items():
            with self.subTest(source=source):
                self.assertEqual(assignment_expression(parse(program(f'A={source};'))), expected)

    def test_error_position(self):
        with self.assertRaises(ParseError) as caught:
            parse(program('A=;'))
        self.assertEqual((caught.exception.token.line, caught.exception.token.column), (3, 3))
        self.assertIn('CONST', caught.exception.expected)

    def test_trace_and_reuse(self):
        parser = Parser()
        tokens = Lexer(program()).scan().tokens
        trace = []
        self.assertEqual(parser.parse(tokens, trace.append), parser.parse(tokens))
        self.assertEqual(trace[-1].action, 'ok')
        self.assertTrue(any(s.action.startswith('r') for s in trace))
        for step in trace:
            self.assertEqual(len(step.states), len(step.symbols) + 1)

    def test_stream_contract(self):
        for tokens in [[], Lexer('A').scan().tokens[:-1], Lexer('1D').scan().tokens,
                       Lexer('').scan().tokens * 2]:
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                Parser().parse(tokens)

    def test_long_and_deep_input(self):
        parse(program('A=' + '(' * 1200 + '1' + ')' * 1200 + ';'))
        tree = parse(program('A=1;' * 1500))
        self.assertGreater(sum(1 for _ in tree.lines()), 1500)

    def test_exported_table_matches_grammar(self):
        action, goto, states, *_ = build()
        self.assertEqual(len(states), 55)
        saved = json.loads((ROOT / 'docs/table.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['action'], action)
        self.assertEqual(saved['goto'], goto)
        self.assertEqual(saved['productions'], [{'lhs': lhs, 'rhs': list(rhs)} for lhs, rhs in PRODUCTIONS])


class CliTests(unittest.TestCase):
    def run_cli(self, args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        return code, out.getvalue(), err.getvalue()

    def test_demo(self):
        code, output, errors = self.run_cli(['--tokens', '--trace', '--tree'])
        self.assertEqual(code, 0)
        self.assertIn('Program', output)
        self.assertFalse(errors)

    def test_error_exit_codes(self):
        for file in ['original.tyap', 'missing_semicolon.tyap']:
            self.assertEqual(self.run_cli([str(ROOT / 'examples/invalid' / file)])[0], 1)
        self.assertEqual(self.run_cli([str(ROOT / 'does-not-exist.tyap')])[0], 2)

    def test_bom_and_tree_export(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / 'source.tyap'
            tree = Path(folder) / 'tree.txt'
            source.write_text(program(), encoding='utf-8-sig')
            self.assertEqual(self.run_cli([str(source), '--tree-output', str(tree)])[0], 0)
            self.assertTrue(tree.read_text(encoding='utf-8').startswith('Program'))


if __name__ == '__main__':
    unittest.main()
