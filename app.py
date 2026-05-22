"""Aplicacion Flask para balancear ecuaciones quimicas.

Este archivo expone una interfaz web y una API JSON pequena. La logica de
quimica y algebra vive en el paquete ``chem_balancer`` para mantener el codigo
modular y facil de ampliar.
"""

from flask import Flask, jsonify, render_template, request

from chem_balancer.balancer import BalanceError, balance_equation


app = Flask(__name__)


@app.get("/")
def index():
    """Muestra la interfaz principal."""
    return render_template("index.html")


@app.post("/api/balance")
def balance_api():
    """Balancea una ecuacion recibida como JSON.

    Espera un cuerpo con la forma ``{"equation": "H2 + O2 -> H2O"}`` y
    devuelve todos los pasos matematicos para que el frontend los renderice.
    """
    data = request.get_json(silent=True) or {}
    equation = str(data.get("equation", "")).strip()

    try:
        result = balance_equation(equation)
        return jsonify({"ok": True, "result": result})
    except BalanceError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True)
