"""Parser de ecuaciones y formulas quimicas.

El parser admite formulas como ``H2O``, ``Fe2O3`` y ``Al2(SO4)3``. Su salida
principal es un conteo de atomos por elemento para cada compuesto.
"""

from collections import defaultdict
from dataclasses import dataclass

from .elements import VALID_ELEMENTS


class ParseError(ValueError):
    """Error de formato o simbolo quimico invalido."""


@dataclass(frozen=True)
class ParsedEquation:
    """Representa una ecuacion separada en reactivos y productos."""

    original: str
    reactants: list[str]
    products: list[str]


def split_equation(equation: str) -> ParsedEquation:
    """Divide una ecuacion en reactivos y productos.

    Valida que exista exactamente una flecha ``->`` y que ambos lados tengan
    compuestos separados por ``+``.
    """
    if not equation:
        raise ParseError("Escribe una ecuacion quimica.")

    if equation.count("->") != 1:
        raise ParseError("La ecuacion debe contener exactamente una flecha ->.")

    left, right = [part.strip() for part in equation.split("->")]
    if not left or not right:
        raise ParseError("La ecuacion debe tener reactivos y productos.")

    reactants = _split_side(left, "reactivos")
    products = _split_side(right, "productos")
    return ParsedEquation(equation, reactants, products)


def _split_side(side: str, side_name: str) -> list[str]:
    """Separa un lado de la ecuacion por signos ``+``."""
    compounds = [compound.strip() for compound in side.split("+")]
    if any(not compound for compound in compounds):
        raise ParseError(f"Hay un compuesto vacio en los {side_name}.")
    return compounds


def parse_formula(formula: str) -> dict[str, int]:
    """Convierte una formula quimica en conteos de atomos.

    Usa una pila de diccionarios para manejar parentesis anidados. Cada grupo
    cerrado se multiplica por el subindice que le sigue.
    """
    if any(char.isspace() for char in formula):
        raise ParseError(f"La formula '{formula}' no debe contener espacios.")
    if not formula:
        raise ParseError("Hay una formula vacia.")

    stack: list[defaultdict[str, int]] = [defaultdict(int)]
    i = 0

    while i < len(formula):
        char = formula[i]

        if char == "(":
            stack.append(defaultdict(int))
            i += 1
            continue

        if char == ")":
            if len(stack) == 1:
                raise ParseError(f"Parentesis de cierre inesperado en '{formula}'.")
            group_counts = stack.pop()
            i += 1
            multiplier, i = _read_number(formula, i)
            for element, count in group_counts.items():
                stack[-1][element] += count * multiplier
            continue

        if char.isupper():
            element, i = _read_element(formula, i)
            if element not in VALID_ELEMENTS:
                raise ParseError(f"Simbolo quimico invalido: {element}.")
            subscript, i = _read_number(formula, i)
            stack[-1][element] += subscript
            continue

        if char.islower():
            raise ParseError(
                f"Simbolo mal escrito cerca de '{char}' en '{formula}'. "
                "Usa mayuscula inicial, por ejemplo Cl."
            )

        if char.isdigit():
            raise ParseError(
                f"Subindice inesperado en '{formula}'. Los numeros deben seguir a un elemento o parentesis."
            )

        raise ParseError(f"Caracter invalido '{char}' en la formula '{formula}'.")

    if len(stack) != 1:
        raise ParseError(f"Parentesis sin cerrar en '{formula}'.")

    counts = dict(stack[0])
    if not counts:
        raise ParseError(f"La formula '{formula}' no contiene elementos validos.")
    return counts


def _read_element(formula: str, index: int) -> tuple[str, int]:
    """Lee un simbolo de elemento desde ``index``."""
    element = formula[index]
    index += 1
    if index < len(formula) and formula[index].islower():
        element += formula[index]
        index += 1
    return element, index


def _read_number(formula: str, index: int) -> tuple[int, int]:
    """Lee un subindice positivo; si no existe, devuelve 1."""
    start = index
    while index < len(formula) and formula[index].isdigit():
        index += 1

    if start == index:
        return 1, index

    number = int(formula[start:index])
    if number <= 0:
        raise ParseError(f"Subindice invalido en '{formula}'.")
    return number, index
