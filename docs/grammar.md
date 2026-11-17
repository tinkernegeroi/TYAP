# Грамматика и магазинный автомат варианта 10

Программа начинается с объявления `VAR`. Затем идёт блок `BEGIN ... END`.
В блоке должна быть хотя бы одна команда. Точка с запятой завершает
объявление и каждую команду. Для `WRITE` принят тот же разделитель, что
для остальных команд: в методичке после записи `WRITE(...)` стоит точка.
В теле `REPEAT` разрешены одно или несколько присваиваний, как в форме из
раздела 2.2 методички. После `UNTIL` идёт условие и точка с запятой.

```text
VAR X,Y: LOGICAL;
BEGIN
    READ(X);
    Y = .NOT. X .OR. 1;
    REPEAT
        X = Y;
    UNTIL X;
    WRITE(X,Y);
END
```

## Правила грамматики

Начальный символ — `Program`. Каждая строка описывает одну часть программы.
Знак `|` читается как «или». Номера правил для свёрток приведены в файле
[Таблица.md](Таблица.md).

```text
Program     → Declaration BEGIN Commands END
Declaration → VAR Names : LOGICAL ;
Names       → ID | Names , ID

Commands    → Command | Commands Command
Command     → Assignment
            | READ ( Names ) ;
            | WRITE ( Names ) ;
            | REPEAT Assignments UNTIL Expr ;
Assignments → Assignment | Assignments Assignment
Assignment  → ID = Expr ;

Expr        → Expr IMP Disjunction | Disjunction
Disjunction → Disjunction OR Conjunction | Conjunction
Conjunction → Conjunction AND Unary | Unary
Unary       → NOT Unary | Atom
Atom        → ( Expr ) | ID | CONST
```

Терминалы — `VAR BEGIN END LOGICAL READ WRITE REPEAT UNTIL NOT AND OR IMP ID CONST ; = ( ) , :`.
Принимаемые значения `CONST` — `0` и `1`. `EOF` — маркер конца ввода,
который добавляет лексер.

У операций четыре уровня, от самого сильного к самому слабому:
`.NOT.`, `.AND.`, `.OR.`, `.IMP.`. Например, в `.NOT. 1 .OR. 1`
сначала собирается `.NOT. 1`, потом выполняется `.OR.`. Скобки
позволяют собрать правую часть в другом порядке. Повтор одной бинарной
операции разбирается слева направо. Это соглашение для грамматики
соответствует алгоритму из методички, где равный приоритет завершает
предыдущую операцию.

