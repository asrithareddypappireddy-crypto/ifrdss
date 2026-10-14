const API_BASE = "";

// ==========================================================================
// NAVIGATION TAB SWITCHING
// ==========================================================================
const navButtons = document.querySelectorAll(".nav-btn");
const tabPanels = document.querySelectorAll(".tab-content");

navButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    navButtons.forEach((b) => b.classList.remove("active"));
    tabPanels.forEach((p) => p.classList.remove("active"));

    btn.classList.add("active");
    const targetId = btn.getAttribute("data-target");
    const targetPanel = document.getElementById(targetId);
    if (targetPanel) {
      targetPanel.classList.add("active");
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
});

// ==========================================================================
// UPLOAD FORM & PIPELINE EXECUTION
// ==========================================================================
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
const priorityBar = document.getElementById("priority-bar");
const analyzeBtn = document.getElementById("analyze-btn");

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!fileInput.files.length) return;
  await processImageFile(fileInput.files[0]);
});

async function processImageFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  statusMsg.innerHTML = "⏳ <span>Running Multi-Cascade CV Pipeline &amp; Triage Analysis... please wait</span>";
  analyzeBtn.disabled = true;
  analyzeBtn.style.opacity = "0.7";
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
    statusMsg.innerHTML = "✅ <span>Analysis complete! Triage metrics and rescue plan generated below.</span>";
    loadHistory();
    // Smooth scroll down to result card
    resultPanel.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    statusMsg.innerHTML = "❌ <span style='color:#dc2626'>Error: " + err.message + "</span>";
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.style.opacity = "1";
  }
}

// Quick Sample Loaders
document.getElementById("load-sample-1").addEventListener("click", async () => {
  try {
    statusMsg.innerHTML = "⏳ Fetching sample flood image 1...";
    const res = await fetch("/sample_flood_image1.jpg");
    const blob = await res.blob();
    const file = new File([blob], "sample_flood_street.jpg", { type: "image/jpeg" });
    await processImageFile(file);
  } catch (e) {
    statusMsg.textContent = "Could not load sample image: " + e.message;
  }
});

document.getElementById("load-sample-2").addEventListener("click", async () => {
  try {
    statusMsg.innerHTML = "⏳ Fetching sample aerial image 2...";
    const res = await fetch("/sample_flood_image2.jpg");
    const blob = await res.blob();
    const file = new File([blob], "sample_flood_aerial.jpg", { type: "image/jpeg" });
    await processImageFile(file);
  } catch (e) {
    statusMsg.textContent = "Could not load sample image: " + e.message;
  }
});

function renderResult(data) {
  resultPanel.hidden = false;
  resultImage.src = `/annotated/${data.annotated_filename}`;
  riskBadge.textContent = `Risk: ${data.risk_level}`;
  riskBadge.className = "badge " + data.risk_level;
  
  resPriority.textContent = `${data.rescue_priority} / 100`;
  if (priorityBar) {
    priorityBar.style.width = `${Math.min(100, Math.max(0, data.rescue_priority))}%`;
  }
  
  resPeople.textContent = `${data.person_count} person(s)`;
  resFlood.textContent = `${(data.flood_ratio * 100).toFixed(1)}%`;
  resDamage.textContent = data.damage_flag
    ? `Possible structural damage (score: ${data.damage_score})`
    : `No significant damage (score: ${data.damage_score})`;
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

// ==========================================================================
// AI MODEL BENCHMARKS & ANALYTICS INTERACTION
// ==========================================================================
const chartTabs = document.querySelectorAll(".chart-tab");
const activeChartImg = document.getElementById("active-chart-img");
const chartCaption = document.getElementById("chart-caption");

const activeChartTitle = document.getElementById("active-chart-title");

const chartMeta = {
  radar: {
    title: "🎯 6-Axis Architecture Radar",
    src: "/advanced_model_radar_benchmark.png",
    caption: "The Proposed IFRDSS Multi-Cascade architecture dominates all baselines in Submerged Victim Recall (95.1%) and real-time CPU speed (38.4 ms), while Linear SVM drops to 58.2%."
  },
  confusion: {
    title: "🟩 Confusion Matrix Grid (Error Analysis)",
    src: "/confusion_matrices_grid.png",
    caption: "False Negative Rate (missed drowning victims) drops drastically from 41.8% in Linear SVM down to only 4.9% in the proposed IFRDSS model."
  },
  pr: {
    title: "📈 Precision-Recall (PR) Curves",
    src: "/precision_recall_curves_multimodel.png",
    caption: "The proposed IFRDSS model sustains high precision even at near-100% recall (mAP = 0.962), ensuring rescue responders are dispatched reliably."
  },
  accuracy: {
    title: "📊 Multi-Metric Accuracy & F1 Comparison",
    src: "/model_accuracy_comparison.png",
    caption: "Proposed IFRDSS achieves 94.2% overall accuracy and 95.1% recall across tested disaster conditions."
  },
  pareto: {
    title: "⚡ Latency vs. Accuracy Pareto Frontier",
    src: "/latency_vs_accuracy_tradeoff.png",
    caption: "Shows that IFRDSS executes at 38.4 ms (~26 FPS) within the sub-60ms real-time emergency triage window on CPU field hardware."
  },
  roc: {
    title: "📉 ROC Curves & AUC Analysis",
    src: "/roc_curves_comparison.png",
    caption: "Proposed IFRDSS achieves the highest Area Under Curve (AUC = 0.978) with optimal true-positive sensitivity and low false alarms."
  }
};

chartTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    chartTabs.forEach((t) => t.classList.remove("active"));
    tab.classList.add("active");
    const key = tab.getAttribute("data-chart");
    if (chartMeta[key]) {
      activeChartImg.style.opacity = "0.2";
      setTimeout(() => {
        activeChartImg.src = chartMeta[key].src;
        chartCaption.innerHTML = chartMeta[key].caption;
        if (activeChartTitle) activeChartTitle.textContent = chartMeta[key].title;
        activeChartImg.style.opacity = "1";
      }, 120);
    }
  });
});

// ==========================================================================
// AHP MULTI-CRITERIA TRIAGE SIMULATOR
// ==========================================================================
const sliderPeople = document.getElementById("slider-w-people");
const sliderFlood = document.getElementById("slider-w-flood");
const sliderDamage = document.getElementById("slider-w-damage");
const valPeople = document.getElementById("val-w-people");
const valFlood = document.getElementById("val-w-flood");
const valDamage = document.getElementById("val-w-damage");
const simScore = document.getElementById("sim-score");
const simRisk = document.getElementById("sim-risk");
const simAsset = document.getElementById("sim-asset");
const simAssetDesc = document.getElementById("sim-asset-desc");
const trackPeople = document.getElementById("track-people");
const trackFlood = document.getElementById("track-flood");
const trackDamage = document.getElementById("track-damage");

// Scenario Presets Definition
const scenarioPresets = {
  balanced: { people: 45, flood: 35, damage: 20 },
  rooftop: { people: 65, flood: 20, damage: 15 },
  flashflood: { people: 25, flood: 60, damage: 15 },
  collapse: { people: 30, flood: 25, damage: 45 }
};

const presetButtons = document.querySelectorAll(".preset-btn");
presetButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    presetButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    const pKey = btn.getAttribute("data-preset");
    if (scenarioPresets[pKey] && sliderPeople && sliderFlood && sliderDamage) {
      sliderPeople.value = scenarioPresets[pKey].people;
      sliderFlood.value = scenarioPresets[pKey].flood;
      sliderDamage.value = scenarioPresets[pKey].damage;
      updateAhpSimulation();
    }
  });
});

async function updateAhpSimulation() {
  if (!sliderPeople) return;
  const wp = parseFloat(sliderPeople.value);
  const wf = parseFloat(sliderFlood.value);
  const wd = parseFloat(sliderDamage.value);

  valPeople.textContent = `${wp}%`;
  valFlood.textContent = `${wf}%`;
  valDamage.textContent = `${wd}%`;

  if (trackPeople) trackPeople.style.width = `${wp}%`;
  if (trackFlood) trackFlood.style.width = `${wf}%`;
  if (trackDamage) trackDamage.style.width = `${wd}%`;

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
      if (simScore) simScore.textContent = data.priority_score;
      if (simRisk) {
        simRisk.textContent = data.risk_level;
        simRisk.className = `sim-risk-tag ${data.risk_level}`;
      }
      if (simAsset && data.rescue_plan) {
        simAsset.textContent = data.rescue_plan.primary_asset;
      }
      if (simAssetDesc && data.rescue_plan) {
        simAssetDesc.textContent = data.rescue_plan.recommended_action || data.rescue_plan.extraction_method || "Tactical response deployed according to AHP multi-criteria priority matrix.";
      }
    }
  } catch (e) {
    console.error("Simulation error", e);
  }
}

if (sliderPeople && sliderFlood && sliderDamage) {
  sliderPeople.addEventListener("input", () => {
    presetButtons.forEach((b) => b.classList.remove("active"));
    updateAhpSimulation();
  });
  sliderFlood.addEventListener("input", () => {
    presetButtons.forEach((b) => b.classList.remove("active"));
    updateAhpSimulation();
  });
  sliderDamage.addEventListener("input", () => {
    presetButtons.forEach((b) => b.classList.remove("active"));
    updateAhpSimulation();
  });
  updateAhpSimulation();
}

// ==========================================================================
// SUBMISSION HISTORY
// ==========================================================================
const historyBody = document.getElementById("history-body");
const sortSelect = document.getElementById("sort-select");
const refreshBtn = document.getElementById("refresh-btn");

async function loadHistory() {
  if (!historyBody) return;
  const sortBy = sortSelect ? sortSelect.value : "timestamp";
  const order = "desc";
  try {
    const resp = await fetch(`${API_BASE}/api/submissions?sort_by=${sortBy}&order=${order}`);
    const rows = await resp.json();
    historyBody.innerHTML = "";
    if (rows.length === 0) {
      historyBody.innerHTML = "<tr><td colspan='8' style='text-align:center;color:#94a3b8;padding:24px'>No submissions recorded yet.</td></tr>";
      return;
    }
    rows.forEach((r) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>#${r.id}</strong></td>
        <td><img class="thumb" src="/uploads/${r.filename}" alt="thumb" onerror="this.src='/sample_flood_image1.jpg'"/></td>
        <td><span class="risk-pill ${r.risk_level}">${r.risk_level}</span></td>
        <td><strong style="color:#1d4ed8">${r.rescue_priority}</strong>/100</td>
        <td>${r.person_count}</td>
        <td>${(r.flood_ratio * 100).toFixed(1)}%</td>
        <td style="font-size:12px;max-width:240px;color:#334155">${r.suggested_response}</td>
        <td style="font-size:11.5px;color:#64748b">${new Date(r.timestamp + "Z").toLocaleString()}</td>
      `;
      historyBody.appendChild(tr);
    });
  } catch (e) {
    console.error("Failed to load history", e);
  }
}

if (sortSelect) sortSelect.addEventListener("change", loadHistory);
if (refreshBtn) refreshBtn.addEventListener("click", loadHistory);

// Initial Load
loadHistory();
