"""Проверка имён и инициализации перед выполнением программы."""
from tyap.diagnostics import SemanticError
from tyap.syntax.tree import Node


def validate(program: Node) -> None:
    block, declaration = program.children
    declared: set[str] = set()
    initialized: set[str] = set()

    for identifier in declaration.children:
        token = identifier.token
        if token.lexeme in declared:
            raise SemanticError(token, f'Повторное объявление {token.lexeme!r}')
        declared.add(token.lexeme)

    def check_name(identifier: Node, *, writing: bool) -> None:
        token = identifier.token
        name = token.lexeme
        if name not in declared:
            raise SemanticError(token, f'Переменная {name!r} не объявлена')
        if writing:
            initialized.add(name)
        elif name not in initialized:
            raise SemanticError(token, f'Переменной {name!r} ещё не присвоено значение')

    def check_expression(expression: Node) -> None:
        pending = [expression]
        while pending:
            node = pending.pop()
            if node.symbol == 'ID':
                check_name(node, writing=False)
            else:
                pending.extend(reversed(node.children))

    def check_block(block: Node) -> None:
        for statement in block.children:
            match statement.symbol:
                case 'READ' | 'WRITE':
                    for identifier in statement.children:
                        check_name(identifier, writing=statement.symbol == 'READ')
                case 'Assignment':
                    target, expression = statement.children
                    check_expression(expression)
                    check_name(target, writing=True)
                case 'REPEAT':
                    # Тело исполняется как минимум один раз, затем проверяется UNTIL.
                    body, condition = statement.children
                    check_block(body)
                    check_expression(condition)
                case _:
                    raise ValueError(f'Неизвестная команда AST: {statement.symbol}')

    check_block(block)
