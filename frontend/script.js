const API_BASE = "";

const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const statusMsg = document.getElementById("status-msg");
const resultPanel = document.getElementById("result-panel");
const resultImage = document.getElementById("result-image");
const riskBadge = document.getElementById("risk-badge");
const resPriority = document.getElementById("res-priority");
const resPeople = document.getElementById("res-people");
const resFlood = document.getElementById("res-flood");
const resDamage = document.getElementById("res-damage");
const resResponse = document.getElementById("res-response");
const historyBody = document.getElementById("history-body");
const sortSelect = document.getElementById("sort-select");
const refreshBtn = document.getElementById("refresh-btn");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) return;

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  statusMsg.textContent = "Analyzing image... please wait.";
  resultPanel.hidden = true;

  try {
    const resp = await fetch(`${API_BASE}/api/submissions`, {
      method: "POST",
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || "Upload failed");
    }
    const data = await resp.json();
    renderResult(data);
    statusMsg.textContent = "Analysis complete.";
    loadHistory();
  } catch (err) {
    statusMsg.textContent = "Error: " + err.message;
  }
});

function renderResult(data) {
  resultPanel.hidden = false;
  resultImage.src = `/annotated/${data.annotated_filename}`;
  riskBadge.textContent = `Risk: ${data.risk_level}`;
  riskBadge.className = "badge " + data.risk_level;
  resPriority.textContent = `${data.rescue_priority} / 100`;
  resPeople.textContent = data.person_count;
  resFlood.textContent = `${(data.flood_ratio * 100).toFixed(1)}%`;
  resDamage.textContent = data.damage_flag
    ? `Possible damage (score ${data.damage_score})`
    : `No significant indicators (score ${data.damage_score})`;
  resResponse.textContent = data.suggested_response;

  if (data.rescue_plan) {
    const p = data.rescue_plan;
    document.getElementById("plan-asset").textContent = p.primary_asset;
    document.getElementById("plan-method").textContent = p.extraction_method;

    const personnelUl = document.getElementById("plan-personnel");
    personnelUl.innerHTML = "";
    p.required_personnel.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      personnelUl.appendChild(li);
    });

    const equipUl = document.getElementById("plan-equipment");
    equipUl.innerHTML = "";
    p.equipment_checklist.forEach((item) => {
      const li = document.createElement("li");
      li.textContent = item;
      equipUl.appendChild(li);
    });

    const stepsOl = document.getElementById("plan-steps");
    stepsOl.innerHTML = "";
    p.execution_steps.forEach((step) => {
      const li = document.createElement("li");
      li.textContent = step;
      stepsOl.appendChild(li);
    });
  }
}

async function loadHistory() {
  const sortBy = sortSelect.value;
  const order = sortBy === "timestamp" ? "desc" : "desc";
  const resp = await fetch(`${API_BASE}/api/submissions?sort_by=${sortBy}&order=${order}`);
  const rows = await resp.json();
  historyBody.innerHTML = "";
  rows.forEach((r) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.id}</td>
      <td><img class="thumb" src="/uploads/${r.filename}" alt="thumb"/></td>
      <td><span class="risk-pill ${r.risk_level}">${r.risk_level}</span></td>
      <td>${r.rescue_priority}</td>
      <td>${r.person_count}</td>
      <td>${(r.flood_ratio * 100).toFixed(1)}%</td>
      <td>${r.suggested_response}</td>
      <td>${new Date(r.timestamp + "Z").toLocaleString()}</td>
    `;
    historyBody.appendChild(tr);
  });
}

sortSelect.addEventListener("change", loadHistory);
refreshBtn.addEventListener("click", loadHistory);

// initial load
loadHistory();
