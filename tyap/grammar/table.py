"""Построение таблицы восходящего разбора для варианта 10."""

import json
from collections import defaultdict, deque
from pathlib import Path


from .rules import BINARY_PRIORITY, EXPRESSION_REDUCTION, PRODUCTIONS, RULES

NONTERMINALS = list(dict.fromkeys(left for left, _ in PRODUCTIONS))
TERMINALS = sorted({symbol for _, right in PRODUCTIONS for symbol in right}
                   - set(NONTERMINALS)) + ["EOF"]
BY_LEFT = defaultdict(list)
for number, (left, _) in enumerate(PRODUCTIONS):
    BY_LEFT[left].append(number)


def edge_sets(reverse=False):
    """First or last terminal for this grammar, whose rules are all nonempty."""
    edges = {symbol: {symbol} for symbol in TERMINALS}
    edges.update({name: set() for name in NONTERMINALS})
    while True:
        size = sum(map(len, edges.values()))
        for left, right in PRODUCTIONS:
            edges[left].update(edges[right[-1 if reverse else 0]])
        if sum(map(len, edges.values())) == size:
            return edges


def following_sets(first):
    follow = {name: set() for name in NONTERMINALS}
    follow["Start"].add("EOF")
    while True:
        size = sum(map(len, follow.values()))
        for left, right in PRODUCTIONS:
            for index, symbol in enumerate(right):
                if symbol in follow:
                    following = first[right[index + 1]] if index + 1 < len(right) else follow[left]
                    follow[symbol].update(following)
        if sum(map(len, follow.values())) == size:
            return follow


def terminal_after(first, last):
    after = {terminal: set() for terminal in TERMINALS}
    for _, right in PRODUCTIONS:
        for left, following in zip(right, right[1:]):
            for terminal in last[left]:
                after[terminal].update(first[following])
    for terminal in last["I"]:
        after[terminal].add("EOF")
    return after


def closure(items):
    seen = set(items)
    pending = deque(seen)
    while pending:
        rule, position = pending.popleft()
        _, right = PRODUCTIONS[rule]
        if position < len(right):
            for next_rule in BY_LEFT.get(right[position], ()):
                item = (next_rule, 0)
                if item not in seen:
                    seen.add(item)
                    pending.append(item)
    return frozenset(seen)


def build():
    first = edge_sets()
    follow = following_sets(first)
    states = [closure([(0, 0)])]
    numbers = {states[0]: 0}
    action = []
    goto = []

    def put(row, symbol, value):
        if symbol in row and row[symbol] != value:
            previous = row[symbol]
            # G → G J G оставляем как в исходной грамматике.
            if (symbol in BINARY_PRIORITY
                    and previous == EXPRESSION_REDUCTION and value.startswith("s")):
                row[symbol] = f"{previous}/{value}"
                return
            raise ValueError(f"Conflict in state {state}, {symbol}: {previous} vs {value}")
        row[symbol] = value

    for state, items in enumerate(states):
        actions, jumps = {}, {}
        action.append(actions)
        goto.append(jumps)
        advances = defaultdict(list)
        for rule, position in sorted(items):
            left, right = PRODUCTIONS[rule]
            if position < len(right):
                advances[right[position]].append((rule, position + 1))
            elif rule == 0:
                put(actions, "EOF", "ok")
            else:
                for terminal in sorted(follow[left]):
                    put(actions, terminal, f"r{rule}")
        for symbol in sorted(advances):
            target = closure(advances[symbol])
            if target not in numbers:
                numbers[target] = len(states)
                states.append(target)
            number = numbers[target]
            if symbol in TERMINALS:
                put(actions, symbol, f"s{number}")
            else:
                jumps[symbol] = number
    return action, goto, states, first, follow


def write_outputs():
    action, goto, states, first, follow = build()
    folder = Path(__file__).resolve().parents[2] / "docs"
    data = {
        "start_state": 0,
        "eof": "EOF",
        "productions": [{"lhs": left, "rhs": right} for left, right in PRODUCTIONS],
        "action": action,
        "goto": goto,
    }
    (folder / "table.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    rows = [
        "# Таблица переходов и расчёт",
        "",
        f"Получено **{len(states)} состояний**. Таблица построена методом SLR.",
        "",
        "Начальное состояние — 0. `sN` — прочитать токен и перейти в N,",
        "`rN` — свернуть правило N, `ok` — принять программу.",
        "В ячейке `rN/sM` автомат выбирает перенос при более сильной входной",
        "бинарной операции. Во всех остальных случаях выполняется свёртка.",
        "Если нужного токена в столбце ACTION нет, это синтаксическая ошибка.",
        "",
        "| Состояние | ACTION по токену | GOTO по нетерминалу |",
        "| --- | --- | --- |",
    ]
    for number, (actions, jumps) in enumerate(zip(action, goto)):
        a = ", ".join(f"`{key}: {value}`" for key, value in sorted(actions.items())) or "—"
        g = ", ".join(f"`{key}: {value}`" for key, value in sorted(jumps.items())) or "—"
        rows.append(f"| {number} | {a} | {g} |")

    def symbols(values):
        return "{" + ", ".join(f"`{x}`" for x in sorted(values)) + "}" if values else "∅"

    rows += ["", "## Нумерация правил", "", "```text"]
    rows += [f"{i:2}. {rule}" for i, rule in enumerate(RULES)]
    rows += ["```", "", "## ПЕРВ и СЛЕД", "",
             "| Нетерминал | ПЕРВ | СЛЕД |", "| --- | --- | --- |"]
    for name in NONTERMINALS:
        rows.append(f"| `{name}` | {symbols(first[name])} | {symbols(follow[name])} |")

    rows += ["", "## ПОСЛЕ", "",
             "Здесь ПОСЛЕ(t) для терминала t означает токены непосредственно справа от него",
             "в потоке правильной программы. Для соседних символов X Y в правой части",
             "правила берём пары из ПОСЛЕДНИЕ(X) × ПЕРВ(Y). Для нетерминалов терминальное",
             "следование приведено в столбце СЛЕД. EOF отмечает конец потока.", "",
             "| Терминал | ПОСЛЕ |", "| --- | --- |"]
    for terminal, successors in terminal_after(first, edge_sets(reverse=True)).items():
        rows.append(f"| `{terminal}` | {symbols(successors)} |")

    rows += ["", "## СВЕРТ", "",
             "В первом столбце правая часть на вершине стека. Во втором номера",
             "возможных свёрток. Окончательную свёртку определяет ячейка ACTION.", "",
             "| Верх стека | Свёртки |", "| --- | --- |"]
    reductions = defaultdict(list)
    for i, (left, right) in enumerate(PRODUCTIONS[1:], 1):
        reductions[right].append(f"`r{i}` → `{left}`")
    for right, choices in reductions.items():
        rows.append(f"| `{' '.join(right)}` | {', '.join(choices)} |")

    rows += ["", "## Ситуации LR(0) по состояниям"]
    for i, items in enumerate(states):
        rows += ["", f"### Состояние {i}", "", "```text"]
        for rule, position in sorted(items):
            left, right = PRODUCTIONS[rule]
            dotted = " ".join((*right[:position], "·", *right[position:]))
            rows.append(f"{rule:2}. {left} → {dotted}")
        rows.append("```")
    (folder / "Таблица.md").write_text("\n".join(rows) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_outputs()
