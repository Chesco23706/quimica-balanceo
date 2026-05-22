"""Orquestador del balanceo quimico."""

from fractions import Fraction
from string import ascii_lowercase

from .linear_algebra import format_matrix, nullspace_integer_vector
from .parser import ParseError, parse_formula, split_equation


class BalanceError(ValueError):
    """Error controlado que puede mostrarse al usuario."""


def balance_equation(equation: str) -> dict:
    """Balancea una ecuacion quimica y devuelve todos los pasos.

    El metodo construye una matriz donde reactivos son positivos y productos
    negativos. El vector de coeficientes buscado esta en el espacio nulo.
    """
    try:
        parsed = split_equation(equation)
        compounds = parsed.reactants + parsed.products
        atom_counts = {compound: parse_formula(compound) for compound in compounds}
    except ParseError as exc:
        raise BalanceError(str(exc)) from exc

    elements = _ordered_elements(atom_counts)
    matrix = _build_matrix(elements, parsed.reactants, parsed.products, atom_counts)

    try:
        coefficients, algebra = nullspace_integer_vector(matrix)
    except ValueError as exc:
        raise BalanceError(str(exc)) from exc

    verification = _verify(elements, parsed.reactants, parsed.products, atom_counts, coefficients)
    if not verification["balanced"]:
        raise BalanceError("La ecuacion no pudo verificarse como balanceada.")

    variables = _variables(len(compounds))
    balanced_equation = _format_balanced(parsed.reactants, parsed.products, coefficients)

    return {
        "original": parsed.original,
        "reactants": parsed.reactants,
        "products": parsed.products,
        "elements": elements,
        "atom_counts": atom_counts,
        "variables": variables,
        "variable_equation": _format_variable_equation(parsed.reactants, parsed.products, variables),
        "linear_equations": _linear_equations(elements, parsed.reactants, parsed.products, atom_counts, variables),
        "matrix": format_matrix(matrix),
        "rref": algebra["rref"],
        "row_steps": algebra["row_steps"],
        "substitutions": algebra["substitutions"],
        "fraction_solution": algebra["fraction_solution"],
        "lcm": algebra["lcm"],
        "gcd": algebra["gcd"],
        "coefficients": dict(zip(variables, coefficients)),
        "coefficient_list": coefficients,
        "verification": verification,
        "balanced_equation": balanced_equation,
    }


def _ordered_elements(atom_counts: dict[str, dict[str, int]]) -> list[str]:
    """Conserva el orden de aparicion de los elementos."""
    elements: list[str] = []
    for counts in atom_counts.values():
        for element in counts:
            if element not in elements:
                elements.append(element)
    return elements


def _build_matrix(
    elements: list[str],
    reactants: list[str],
    products: list[str],
    atom_counts: dict[str, dict[str, int]],
) -> list[list[Fraction]]:
    """Construye la matriz de conservacion de atomos."""
    matrix: list[list[Fraction]] = []
    for element in elements:
        row = []
        for compound in reactants:
            row.append(Fraction(atom_counts[compound].get(element, 0)))
        for compound in products:
            row.append(Fraction(-atom_counts[compound].get(element, 0)))
        matrix.append(row)
    return matrix


def _variables(amount: int) -> list[str]:
    """Genera nombres de variables a, b, c... y xN si hacen falta mas."""
    names = list(ascii_lowercase)
    if amount <= len(names):
        return names[:amount]
    return names + [f"x{i}" for i in range(27, amount + 1)]


def _format_variable_equation(reactants: list[str], products: list[str], variables: list[str]) -> str:
    """Muestra la ecuacion usando variables como coeficientes."""
    left = " + ".join(f"{var}{compound}" for var, compound in zip(variables, reactants))
    right_vars = variables[len(reactants):]
    right = " + ".join(f"{var}{compound}" for var, compound in zip(right_vars, products))
    return f"{left} -> {right}"


def _linear_equations(
    elements: list[str],
    reactants: list[str],
    products: list[str],
    atom_counts: dict[str, dict[str, int]],
    variables: list[str],
) -> list[dict[str, str]]:
    """Crea ecuaciones de conservacion en forma legible."""
    equations = []
    for element in elements:
        left_terms = [
            _term(atom_counts[compound].get(element, 0), variables[index])
            for index, compound in enumerate(reactants)
            if atom_counts[compound].get(element, 0)
        ]
        right_terms = [
            _term(atom_counts[compound].get(element, 0), variables[len(reactants) + index])
            for index, compound in enumerate(products)
            if atom_counts[compound].get(element, 0)
        ]
        equations.append(
            {
                "element": element,
                "equation": f"{' + '.join(left_terms)} = {' + '.join(right_terms)}",
            }
        )
    return equations


def _term(count: int, variable: str) -> str:
    """Formatea un termino como a o 2a."""
    return variable if count == 1 else f"{count}{variable}"


def _verify(
    elements: list[str],
    reactants: list[str],
    products: list[str],
    atom_counts: dict[str, dict[str, int]],
    coefficients: list[int],
) -> dict:
    """Calcula atomos totales en ambos lados para verificar el resultado."""
    reactant_coeffs = coefficients[: len(reactants)]
    product_coeffs = coefficients[len(reactants):]
    reactant_totals = {}
    product_totals = {}

    for element in elements:
        reactant_totals[element] = sum(
            coeff * atom_counts[compound].get(element, 0)
            for coeff, compound in zip(reactant_coeffs, reactants)
        )
        product_totals[element] = sum(
            coeff * atom_counts[compound].get(element, 0)
            for coeff, compound in zip(product_coeffs, products)
        )

    return {
        "reactants": reactant_totals,
        "products": product_totals,
        "balanced": reactant_totals == product_totals,
    }


def _format_balanced(reactants: list[str], products: list[str], coefficients: list[int]) -> str:
    """Construye la ecuacion balanceada final."""
    left = _format_side(reactants, coefficients[: len(reactants)])
    right = _format_side(products, coefficients[len(reactants):])
    return f"{left} -> {right}"


def _format_side(compounds: list[str], coefficients: list[int]) -> str:
    """Formatea un lado de la ecuacion, omitiendo coeficiente 1."""
    terms = []
    for coeff, compound in zip(coefficients, compounds):
        terms.append(compound if coeff == 1 else f"{coeff}{compound}")
    return " + ".join(terms)
