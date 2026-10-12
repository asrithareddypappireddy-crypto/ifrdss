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

// ==========================================================================
// ADVANCED AI MODEL BENCHMARKS & ANALYTICS INTERACTION
// ==========================================================================
const chartTabs = document.querySelectorAll(".chart-tab");
const activeChartImg = document.getElementById("active-chart-img");
const chartCaption = document.getElementById("chart-caption");

const chartMeta = {
  radar: {
    src: "/advanced_model_radar_benchmark.png",
    caption: "<strong>Figure 1: 6-Dimensional Radar Trade-Off.</strong> The Proposed IFRDSS Multi-Cascade architecture dominates all baselines on Submerged Victim Recall (95.1%) and real-time CPU speed (38.4 ms), while Linear SVM fails on submerged limbs (58.2%)."
  },
  confusion: {
    src: "/confusion_matrices_grid.png",
    caption: "<strong>Figure 2: Confusion Matrices on Flood Imagery.</strong> The False Negative Rate (missed drowning victims) drops drastically from 41.8% in Linear SVM down to only 4.9% in the proposed IFRDSS model."
  },
  pr: {
    src: "/precision_recall_curves_multimodel.png",
    caption: "<strong>Figure 3: Precision-Recall Curves.</strong> The proposed IFRDSS model sustains high precision even at near-100% recall (mAP@50 = 0.962), ensuring search-and-rescue teams don't miss occluded survivors."
  },
  accuracy: {
    src: "/model_accuracy_comparison.png",
    caption: "<strong>Figure 4: Multi-Metric Comparison (Accuracy, Precision, Recall, F1).</strong> Proposed IFRDSS achieves 94.2% accuracy and 95.1% recall across tested disaster conditions."
  },
  pareto: {
    src: "/latency_vs_accuracy_tradeoff.png",
    caption: "<strong>Figure 5: Latency vs. Accuracy Pareto Frontier.</strong> Shows that IFRDSS executes at 38.4 ms (~26 FPS) within the sub-60ms real-time emergency window on CPU field hardware."
  },
  roc: {
    src: "/roc_curves_comparison.png",
    caption: "<strong>Figure 6: ROC & AUC Curves.</strong> Proposed IFRDSS achieves the highest Area Under Curve (AUC = 0.978) with optimal true-positive sensitivity and low false alarms."
  }
};

chartTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    chartTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const key = tab.getAttribute("data-chart");
    if (chartMeta[key]) {
      activeChartImg.src = chartMeta[key].src;
      chartCaption.innerHTML = chartMeta[key].caption;
    }
  });
});

// AHP Multi-Criteria Simulator
const sliderPeople = document.getElementById("slider-w-people");
const sliderFlood = document.getElementById("slider-w-flood");
const sliderDamage = document.getElementById("slider-w-damage");
const valPeople = document.getElementById("val-w-people");
const valFlood = document.getElementById("val-w-flood");
const valDamage = document.getElementById("val-w-damage");
const simScore = document.getElementById("sim-score");
const simRisk = document.getElementById("sim-risk");
const simAsset = document.getElementById("sim-asset");

async function updateAhpSimulation() {
  const wp = parseFloat(sliderPeople.value);
  const wf = parseFloat(sliderFlood.value);
  const wd = parseFloat(sliderDamage.value);

  valPeople.textContent = `${wp}%`;
  valFlood.textContent = `${wf}%`;
  valDamage.textContent = `${wd}%`;

  try {
    const res = await fetch(`${API_BASE}/api/simulate-priority`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        flood_ratio: 0.35,
        person_count: 3,
        damage_score: 0.25,
        weight_people: wp,
        weight_flood: wf,
        weight_damage: wd
      })
    });
    if (res.ok) {
      const data = await res.json();
      simScore.textContent = data.priority_score;
      simRisk.textContent = data.risk_level;
      simAsset.textContent = data.rescue_plan.primary_asset;
    }
  } catch (e) {
    console.error("Simulation error", e);
  }
}

if (sliderPeople && sliderFlood && sliderDamage) {
  sliderPeople.addEventListener("input", updateAhpSimulation);
  sliderFlood.addEventListener("input", updateAhpSimulation);
  sliderDamage.addEventListener("input", updateAhpSimulation);
  updateAhpSimulation();
}

// initial load
loadHistory();

