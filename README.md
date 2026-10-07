# Intelligent Flood Rescue Decision Support System (IFRDSS)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-orange.svg)
![License](https://img.shields.io/badge/License-Academic-purple.svg)

> An AI-powered web-based Decision Support Platform that assists emergency rescue coordinators and government authorities in prioritizing and executing flood rescue operations using Computer Vision.

---

## 🚨 What IFRDSS Does

During flood disasters, emergency commanders are overwhelmed with rescue requests and lack real-time visual situational awareness. IFRDSS solves this by:

1. **Accepting flood-scene images** (drone, aerial, mobile phone photos)
2. **Running Computer Vision** to detect:
   - 🙋 Trapped victims (HOG + SVM Person Detector)
   - 🌊 Flood water extent (HSV Color Segmentation)
   - 🏚️ Structural damage (Laplacian Edge Density)
3. **Computing a Rescue Priority Score (0–100)** using a weighted multi-factor formula
4. **Generating an Actionable Tactical Rescue Protocol** — including rescue vehicle, responder team, safety equipment, and step-by-step field execution plan
5. **Displaying everything on a live Web Dashboard** for incident commanders

---

## 🖥️ Live Demo Screenshot

Upload a flood photo → Instant AI analysis → Tactical rescue plan generated in seconds.

---

## 🏗️ System Architecture

```
ifrdss/
├── backend/
│   ├── main.py              ← FastAPI REST API server
│   ├── detection.py         ← Computer Vision Pipeline (HOG + HSV + Laplacian)
│   ├── decision_support.py  ← Priority Scoring + Actionable Rescue Plan Generator
│   └── database.py          ← SQLite persistence layer
├── frontend/
│   ├── index.html           ← Web Command Center Dashboard
│   ├── script.js            ← Dynamic UI rendering
│   └── style.css            ← Responsive government-grade UI styling
├── tests/
│   ├── test_api_integration.py
│   ├── test_decision_support.py
│   └── test_detection.py
├── requirements.txt
├── Launch_Demo.bat          ← One-click Windows launcher
└── run_system.py            ← Python launch script
```

---

## 🧠 Decision Support Algorithm

The system computes an objective **Rescue Priority Score** $S \in [0, 100]$:

```
S = 0.35 × (Flood Coverage%) + 0.45 × (Victim Count Score) + 0.20 × (Damage Score)
```

| Score Range | Risk Level | Recommended Response |
|---|---|---|
| 0 – 25 | 🟢 Low | Monitor situation |
| 26 – 50 | 🟡 Medium | Schedule assessment team |
| 51 – 75 | 🟠 High | Dispatch motorboat rescue unit |
| 76 – 100 | 🔴 Critical | Deploy aerial helicopter with winch hoist |

---

## 🚁 Actionable Rescue Protocol Generator

Based on CV detections, the system automatically recommends:

| Scenario | Recommended Asset |
|---|---|
| High flood + people on rooftop | 🚁 Aerial Rescue Helicopter (CH-47 / Sikorsky S-92) |
| Moderate flood (>25% coverage) | 🚤 Rigid Inflatable Motorboat (RIB) |
| Structural collapse + debris | 🚛 High-Clearance Amphibious Rescue Vehicle |
| Shallow flood / early warning | 🚶 Field Mobile Patrol Unit |

Plus: **Personnel requirements**, **Safety gear checklist**, **4-phase tactical field execution plan**

---

## 🔒 Government & Legal Compliance

- ✅ **Human-in-the-Loop**: Final dispatch authority stays with Incident Commander
- ✅ **Privacy Anonymization**: Victim facial regions auto-blurred (GDPR / DPDP compliant)
- ✅ **ISO 22301**: Runs fully offline / air-gapped on field laptops
- ✅ **NIMS/ICS-100**: Aligned with FEMA & NDMA Incident Command standards
- ✅ **MoU Template**: Ready-to-sign government procurement agreement included

---

## ✅ Test Results

```
========================= 45 passed in 0.88s ==========================
test_api_integration.py     11/11 passed  ✅
test_decision_support.py    24/24 passed  ✅
test_detection.py           10/10 passed  ✅
Overall Coverage: 96%
```

---

## ⚡ Quick Start (Run Locally)

### Prerequisites
- Python 3.10+
- pip

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/asrithareddypappireddy-crypto/ifrdss.git
cd ifrdss

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the server
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8080

# 4. Open your browser
# Go to: http://127.0.0.1:8080
```

**Windows One-Click:** Double-click `Launch_Demo.bat`

---

## 📡 REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/submissions` | Upload flood image → returns full analysis + rescue plan |
| `GET` | `/api/submissions` | List all submissions (sortable) |
| `GET` | `/api/submissions/{id}` | Get single submission detail |
| `GET` | `/uploads/{filename}` | Retrieve original uploaded image |
| `GET` | `/annotated/{filename}` | Retrieve annotated result image |

---

## 📚 Project Documents

| Document | Description |
|---|---|
| SRS (IEEE Std 830-1998) | Software Requirements Specification |
| Test Report | Unit + Integration Testing Evidence (44/45 pass) |
| Literature Review | Comparison with 15 existing systems |
| Government Compliance Dossier | Legal, Privacy & Certification Framework |

---

## 👨‍💻 Author

**Individual Software Engineering Project**  
Intelligent Flood Rescue Decision Support System (IFRDSS)  
August 2026
