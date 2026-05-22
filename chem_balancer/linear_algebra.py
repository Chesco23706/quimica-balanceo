"""Algebra lineal exacta para balancear ecuaciones.

Todas las operaciones se hacen con ``Fraction`` para evitar errores numericos.
"""

from fractions import Fraction
from math import gcd
from functools import reduce


def format_fraction(value: Fraction) -> str:
    """Devuelve una fraccion legible."""
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def format_matrix(matrix: list[list[Fraction]]) -> list[list[str]]:
    """Convierte una matriz de fracciones a texto para la interfaz."""
    return [[format_fraction(value) for value in row] for row in matrix]


def rref(matrix: list[list[Fraction]]) -> tuple[list[list[Fraction]], list[int], list[str]]:
    """Calcula la forma reducida por filas y registra las operaciones.

    Devuelve la matriz reducida, las columnas pivote y una lista de pasos.
    """
    working = [row[:] for row in matrix]
    rows = len(working)
    cols = len(working[0]) if rows else 0
    pivot_columns: list[int] = []
    steps: list[str] = []
    pivot_row = 0

    for col in range(cols):
        pivot = next((r for r in range(pivot_row, rows) if working[r][col] != 0), None)
        if pivot is None:
            continue

        if pivot != pivot_row:
            working[pivot_row], working[pivot] = working[pivot], working[pivot_row]
            steps.append(f"Intercambiar F{pivot_row + 1} <-> F{pivot + 1}.")

        pivot_value = working[pivot_row][col]
        if pivot_value != 1:
            working[pivot_row] = [value / pivot_value for value in working[pivot_row]]
            steps.append(f"F{pivot_row + 1} = F{pivot_row + 1} / {format_fraction(pivot_value)}.")

        for row in range(rows):
            if row == pivot_row:
                continue
            factor = working[row][col]
            if factor != 0:
                working[row] = [
                    value - factor * pivot_value_in_row
                    for value, pivot_value_in_row in zip(working[row], working[pivot_row])
                ]
                sign = "-" if factor > 0 else "+"
                steps.append(
                    f"F{row + 1} = F{row + 1} {sign} {format_fraction(abs(factor))}F{pivot_row + 1}."
                )

        pivot_columns.append(col)
        pivot_row += 1
        if pivot_row == rows:
            break

    return working, pivot_columns, steps


def nullspace_integer_vector(matrix: list[list[Fraction]]) -> tuple[list[int], dict]:
    """Obtiene un vector entero no nulo en el espacio nulo de la matriz.

    Para ecuaciones quimicas, el vector nulo representa los coeficientes. Si el
    sistema tiene varias variables libres, se asigna 1 a todas ellas y luego se
    escalan los resultados al minimo comun entero.
    """
    reduced, pivots, row_steps = rref(matrix)
    cols = len(matrix[0]) if matrix else 0
    free_columns = [col for col in range(cols) if col not in pivots]

    if not free_columns:
        raise ValueError("El sistema no tiene variables libres para balancear.")

    solution = [Fraction(0) for _ in range(cols)]
    substitutions: list[str] = []

    for col in free_columns:
        solution[col] = Fraction(1)
        substitutions.append(f"Tomar variable libre x{col + 1} = 1.")

    for row, pivot_col in enumerate(pivots):
        value = -sum(reduced[row][free] * solution[free] for free in free_columns)
        solution[pivot_col] = value
        substitutions.append(
            f"x{pivot_col + 1} = {format_fraction(value)} al sustituir las variables libres."
        )

    if all(value == 0 for value in solution):
        raise ValueError("No se encontro una solucion no trivial.")

    if any(value < 0 for value in solution):
        solution = [-value for value in solution]
        substitutions.append("Multiplicar todo el vector por -1 para obtener coeficientes positivos.")

    if any(value <= 0 for value in solution):
        raise ValueError("La ecuacion no puede balancearse con coeficientes positivos.")

    denominator_lcm = reduce(_lcm, (value.denominator for value in solution), 1)
    integers = [int(value * denominator_lcm) for value in solution]
    common_divisor = reduce(gcd, (abs(value) for value in integers))
    integers = [value // common_divisor for value in integers]

    metadata = {
        "rref": format_matrix(reduced),
        "pivot_columns": pivots,
        "free_columns": free_columns,
        "row_steps": row_steps,
        "substitutions": substitutions,
        "fraction_solution": [format_fraction(value) for value in solution],
        "lcm": denominator_lcm,
        "gcd": common_divisor,
    }
    return integers, metadata


def _lcm(a: int, b: int) -> int:
    """Minimo comun multiplo."""
    return abs(a * b) // gcd(a, b)
