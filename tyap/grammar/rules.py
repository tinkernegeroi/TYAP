"""Продукции варианта 10 на уровне токенов лексера."""

# Лексер уже распознаёт L целиком. Значения M различаются по тексту токена.
RULES = (
    'Start -> I',
    'I -> BEGIN B A END',
    'A -> P',
    'B -> VAR C : LOGICAL ;',
    'C -> L',
    'C -> L , C',
    'P -> E',
    'P -> E P',
    'P -> O',
    'P -> O P',
    'D -> E',
    'D -> E D',
    'E -> L = F ;',
    'F -> H G',
    'F -> G',
    'G -> ( F )',
    'G -> K',
    'G -> G J G',
    'H -> NOT',
    'J -> AND',
    'J -> OR',
    'J -> IMP',
    'K -> L',
    'K -> M',
    'L -> ID',
    'M -> 0',
    'M -> 1',
    'O -> READ ( C ) ;',
    'O -> REPEAT D UNTIL F ;',
    'O -> WRITE ( C ) ;',
)

PRODUCTIONS = tuple((left, tuple(right.split())) for left, right in
                    (rule.split(' -> ') for rule in RULES))
EXPRESSION_REDUCTION = f'r{RULES.index("G -> G J G")}'
BINARY_PRIORITY = {'IMP': 1, 'OR': 2, 'AND': 3}
