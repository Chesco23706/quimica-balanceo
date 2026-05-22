const form = document.querySelector("#balance-form");
const input = document.querySelector("#equation");
const result = document.querySelector("#result");
const errorBox = document.querySelector("#error");
const historyBox = document.querySelector("#history");
const exportBtn = document.querySelector("#export-btn");
const themeToggle = document.querySelector("#theme-toggle");

let lastResult = null;
let history = JSON.parse(localStorage.getItem("equation-history") || "[]");

renderHistory();
restoreTheme();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  await balance(input.value.trim());
});

document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => {
    input.value = button.dataset.example;
    balance(input.value);
  });
});

themeToggle.addEventListener("change", () => {
  document.body.classList.toggle("dark", themeToggle.checked);
  localStorage.setItem("dark-theme", themeToggle.checked ? "1" : "0");
});

exportBtn.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([buildExportText(lastResult)], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "balanceo-quimico.txt";
  link.click();
  URL.revokeObjectURL(url);
});

async function balance(equation) {
  errorBox.classList.add("hidden");
  result.classList.add("hidden");
  result.innerHTML = "";

  try {
    const response = await fetch("/api/balance", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ equation }),
    });
    const data = await response.json();
    if (!data.ok) throw new Error(data.error);

    lastResult = data.result;
    exportBtn.disabled = false;
    saveHistory(equation);
    renderResult(data.result);
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("hidden");
    exportBtn.disabled = true;
  }
}

function renderResult(data) {
  const sections = [
    finalSection(data),
    listSection("1. Ecuación original", [data.original]),
    splitSection(data),
    listSection("3. Elementos detectados", data.elements),
    atomCountSection(data),
    listSection("5. Asignación de variables", [data.variable_equation]),
    equationsSection(data),
    matrixSection("7. Conversión del sistema a matriz", data.matrix),
    resolutionSection(data),
    coefficientsSection(data),
    verificationSection(data),
  ];

  result.innerHTML = sections.join("");
  result.classList.remove("hidden");
}

function finalSection(data) {
  return `
    <article class="step balanced">
      <h3>11. Ecuación balanceada final</h3>
      <p class="final-equation">${escapeHtml(data.balanced_equation)}</p>
    </article>
  `;
}

function splitSection(data) {
  return `
    <article class="step">
      <h3>2. Separación de reactivos y productos</h3>
      <div class="verification-grid">
        <div class="verify-card"><strong>Reactivos</strong><ul>${data.reactants.map(item).join("")}</ul></div>
        <div class="verify-card"><strong>Productos</strong><ul>${data.products.map(item).join("")}</ul></div>
      </div>
    </article>
  `;
}

function atomCountSection(data) {
  const compounds = [...data.reactants, ...data.products];
  return `
    <article class="step">
      <h3>4. Conteo de átomos por compuesto</h3>
      <div class="compound-grid">
        ${compounds.map((compound) => `
          <div class="compound">
            <strong>${escapeHtml(compound)}</strong>
            ${Object.entries(data.atom_counts[compound]).map(([element, amount]) => `<div>${escapeHtml(element)} = ${amount}</div>`).join("")}
          </div>
        `).join("")}
      </div>
    </article>
  `;
}

function equationsSection(data) {
  return `
    <article class="step">
      <h3>6. Construcción del sistema de ecuaciones</h3>
      <ul>${data.linear_equations.map((entry) => item(`Para ${entry.element}: ${entry.equation}`)).join("")}</ul>
    </article>
  `;
}

function resolutionSection(data) {
  return `
    <article class="step">
      <h3>8. Resolución paso a paso del sistema</h3>
      <p>Se reduce la matriz con operaciones elementales de fila:</p>
      <ol>${data.row_steps.map(item).join("")}</ol>
      ${matrixMarkup(data.rref)}
      <p>Después se obtiene un vector del espacio nulo:</p>
      <ol>${data.substitutions.map(item).join("")}</ol>
      <p>Solución fraccionaria: (${data.fraction_solution.map(escapeHtml).join(", ")}).</p>
      <p>Se multiplica por m.c.m. de denominadores = ${data.lcm} y se divide por m.c.d. = ${data.gcd} para obtener enteros mínimos.</p>
    </article>
  `;
}

function coefficientsSection(data) {
  return `
    <article class="step">
      <h3>9. Coeficientes encontrados</h3>
      <div class="chips">
        ${Object.entries(data.coefficients).map(([variable, value]) => `<span class="chip">${escapeHtml(variable)} = ${value}</span>`).join("")}
      </div>
    </article>
  `;
}

function verificationSection(data) {
  return `
    <article class="step">
      <h3>10. Verificación final</h3>
      <div class="verification-grid">
        <div class="verify-card"><strong>Reactivos</strong>${totals(data.verification.reactants)}</div>
        <div class="verify-card"><strong>Productos</strong>${totals(data.verification.products)}</div>
      </div>
      <p>${data.verification.balanced ? "Balance correcto." : "El balance no coincide."}</p>
    </article>
  `;
}

function listSection(title, values) {
  return `<article class="step"><h3>${title}</h3><ul>${values.map(item).join("")}</ul></article>`;
}

function matrixSection(title, matrix) {
  return `<article class="step"><h3>${title}</h3>${matrixMarkup(matrix)}</article>`;
}

function matrixMarkup(matrix) {
  return `
    <div class="matrix-wrap">
      <table class="matrix">
        <tbody>${matrix.map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell)}</td>`).join("")}</tr>`).join("")}</tbody>
      </table>
    </div>
  `;
}

function totals(values) {
  return Object.entries(values).map(([element, amount]) => `<div>${escapeHtml(element)} = ${amount}</div>`).join("");
}

function item(value) {
  return `<li>${escapeHtml(value)}</li>`;
}

function saveHistory(equation) {
  history = [equation, ...history.filter((entry) => entry !== equation)].slice(0, 8);
  localStorage.setItem("equation-history", JSON.stringify(history));
  renderHistory();
}

function renderHistory() {
  historyBox.innerHTML = history.length
    ? history.map((entry) => `<button type="button">${escapeHtml(entry)}</button>`).join("")
    : "<p>No hay ecuaciones todavía.</p>";

  historyBox.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      input.value = button.textContent;
      balance(input.value);
    });
  });
}

function restoreTheme() {
  const enabled = localStorage.getItem("dark-theme") === "1";
  themeToggle.checked = enabled;
  document.body.classList.toggle("dark", enabled);
}

function buildExportText(data) {
  return [
    `Ecuacion original: ${data.original}`,
    `Ecuacion balanceada: ${data.balanced_equation}`,
    "",
    "Reactivos:",
    ...data.reactants.map((compound) => `- ${compound}`),
    "Productos:",
    ...data.products.map((compound) => `- ${compound}`),
    "",
    "Matriz:",
    ...data.matrix.map((row) => `[ ${row.join("  ")} ]`),
    "",
    "Operaciones:",
    ...data.row_steps.map((step) => `- ${step}`),
    "",
    "Coeficientes:",
    ...Object.entries(data.coefficients).map(([variable, value]) => `${variable} = ${value}`),
  ].join("\n");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
