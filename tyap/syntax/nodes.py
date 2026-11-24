"""Построение абстрактного синтаксического дерева из дерева свёрток."""
from .tree import Node


def _list_items(node: Node, tail_index: int):
    """Разворачивает праворекурсивный список C, D или P по порядку."""
    while True:
        yield node.children[0]
        if len(node.children) == 1:
            return
        node = node.children[tail_index]


def _ast_parts(node: Node) -> tuple[str, tuple[Node, ...]]:
    children = node.children
    match node.symbol:
        case 'I':
            return 'Program', (children[2], children[1])
        case 'A':
            return 'Block', tuple(_list_items(children[0], 1))
        case 'B':
            return 'Declaration LOGICAL', tuple(_list_items(children[1], 2))
        case 'E':
            return 'Assignment', (children[0], children[2])
        case 'O':
            operation = children[0].symbol
            if operation == 'REPEAT':
                return 'REPEAT', (children[1], children[3])
            return operation, tuple(_list_items(children[2], 2))
        case 'D':
            return 'Body', tuple(_list_items(node, 1))
        case 'F' if len(children) == 2:
            return 'Unary NOT', (children[1],)
        case 'G' if len(children) == 3:
            if children[0].symbol == '(':
                return '', (children[1],)
            return f'Binary {children[1].children[0].symbol}', (children[0], children[2])
        case _:
            return '', children


def build_ast(tree: Node) -> Node:
    """Удаляет служебные нетерминалы и разделители, сохраняя структуру команд."""
    result: list[Node] = []
    pending: list[Node | tuple[str, int]] = [tree]
    while pending:
        item = pending.pop()
        if isinstance(item, tuple):
            symbol, size = item
            children = tuple(result[-size:])
            del result[-size:]
            result.append(Node(symbol, children))
        elif item.token is not None:
            result.append(item)
        else:
            symbol, children = _ast_parts(item)
            if symbol:
                pending.append((symbol, len(children)))
            pending.extend(reversed(children))
    return result[0]
