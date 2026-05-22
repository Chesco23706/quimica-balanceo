# Balanceador de ecuaciones quimicas

Aplicacion web en Flask que balancea ecuaciones quimicas con sistemas de ecuaciones lineales y algebra matricial exacta.

## Caracteristicas

- Detecta reactivos, productos, elementos y atomos por compuesto.
- Acepta subindices y parentesis, por ejemplo `Al2(SO4)3`.
- Valida flecha `->`, parentesis, formulas vacias y simbolos quimicos reales.
- Construye la matriz de conservacion de atomos.
- Resuelve con eliminacion Gauss-Jordan usando fracciones exactas.
- Muestra operaciones de fila, sustituciones, coeficientes enteros minimos y verificacion.
- Incluye historial local, modo oscuro, exportacion de resultados y diseno adaptable.

## Instalacion

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Abre la app en `http://127.0.0.1:5000`.

## Despliegue en Vercel

El proyecto ya incluye:

- `api/index.py`: entrypoint para el runtime Python de Vercel.
- `vercel.json`: rutas para servir Flask y archivos estaticos.

Desde la raiz del proyecto:

```bash
npm install -g vercel
vercel login
vercel
vercel --prod
```

## Subir a GitHub

Si el repositorio todavia no tiene remoto:

```bash
git remote add origin https://github.com/TU_USUARIO/NOMBRE_DEL_REPO.git
git branch -M main
git push -u origin main
```

## Ejemplos para probar

- `H2 + O2 -> H2O`
- `Fe + O2 -> Fe2O3`
- `C3H8 + O2 -> CO2 + H2O`
- `Na + Cl2 -> NaCl`
- `Al + O2 -> Al2O3`
- `KMnO4 + HCl -> KCl + MnCl2 + H2O + Cl2`

## Como funciona

1. Se separa la ecuacion en reactivos y productos.
2. Cada formula se analiza con una pila para resolver grupos con parentesis.
3. Por cada elemento se crea una ecuacion de conservacion de atomos.
4. Las ecuaciones se convierten en una matriz donde reactivos son positivos y productos negativos.
5. Se busca un vector no nulo del espacio nulo de la matriz.
6. La solucion fraccionaria se escala al minimo conjunto de coeficientes enteros positivos.
7. Se verifica que el total de atomos de cada elemento sea igual en ambos lados.

## Estructura

- `app.py`: servidor Flask y API.
- `chem_balancer/parser.py`: parser de ecuaciones y formulas.
- `chem_balancer/linear_algebra.py`: reduccion por filas y espacio nulo.
- `chem_balancer/balancer.py`: construccion del procedimiento completo.
- `templates/index.html`: interfaz principal.
- `static/styles.css`: estilos responsivos y modo oscuro.
- `static/app.js`: comunicacion con API, historial y exportacion.
