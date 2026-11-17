"""Единственный источник правил исправленной грамматики варианта 10."""

# Rule numbers are the line indices. Rule 0 is used only for acceptance.
RULES = [
    "Start -> Program",
    "Program -> Declaration BEGIN Commands END",
    "Declaration -> VAR Names : LOGICAL ;",
    "Names -> ID",
    "Names -> Names , ID",
    "Commands -> Command",
    "Commands -> Commands Command",
    "Command -> Assignment",
    "Command -> READ ( Names ) ;",
    "Command -> WRITE ( Names ) ;",
    "Command -> REPEAT Assignments UNTIL Expr ;",
    "Assignments -> Assignment",
    "Assignments -> Assignments Assignment",
    "Assignment -> ID = Expr ;",
    "Expr -> Expr IMP Disjunction",
    "Expr -> Disjunction",
    "Disjunction -> Disjunction OR Conjunction",
    "Disjunction -> Conjunction",
    "Conjunction -> Conjunction AND Unary",
    "Conjunction -> Unary",
    "Unary -> NOT Unary",
    "Unary -> Atom",
    "Atom -> ( Expr )",
    "Atom -> ID",
    "Atom -> CONST",
]

PRODUCTIONS = [tuple(rule.split(" -> ")) for rule in RULES]
PRODUCTIONS = [(left, tuple(right.split())) for left, right in PRODUCTIONS]
