# IFRDSS - Project Viva & Defense Presentation Guide

Use this presentation outline and Q&A reference to present and defend your **Intelligent Flood Rescue Decision Support System (IFRDSS)** project in front of evaluators, professors, or stakeholders.

---

## 1. 10-Slide Project Presentation Outline

| Slide # | Slide Title | Key Content & Speaking Points |
|---|---|---|
| **Slide 1** | **Title & Introduction** | Project Name: Intelligent Flood Rescue Decision Support System (IFRDSS)<br>Domain: AI/CV Disaster Management & Decision Support Systems |
| **Slide 2** | **Problem Statement** | During severe flood disasters, emergency call centers are overwhelmed with unstructured SOS requests. Rescue commanders lack real-time visual situational awareness and quantitative priority ranking to allocate scarce rescue assets (boats, helicopters). |
| **Slide 3** | **Objectives & Scope** | Build an automated web platform that ingests aerial/street flood imagery, extracts key risk indicators using Computer Vision, calculates an objective rescue priority score, and assists commanders in dispatching resources. |
| **Slide 4** | **Software Requirements (SRS)** | IEEE Std 830-1998 compliant requirements covering image upload (FR-1), CV feature extraction (FR-2), decision support scoring (FR-3), web dashboard (FR-4), and SQLite spatial storage. |
| **Slide 5** | **System Architecture (SDS)** | 5-tier architecture: Presentation Tier (Web Dashboard), Gateway Tier (FastAPI), Intelligence Tier (CV + Decision Engine), Domain Tier (Services), Persistence Tier (SQLite + Disk Storage). |
| **Slide 6** | **StarUML Design Models** | Highlights from Class Diagram, Sequence Diagram (SOS workflow), Activity Diagram (decision tree), and Layered Architecture Diagram. |
| **Slide 7** | **Computer Vision & AI Module** | HOG + Linear SVM for victim detection, HSV color space thresholding for flood extent, and Laplacian variance for structural damage quantification. |
| **Slide 8** | **Decision Support Scoring** | Weighted priority formula combining flood extent (35%), victim count (45%), and structural damage (20%) to yield a 0-100 score and risk category (Low, Medium, High, Critical). |
| **Slide 9** | **Testing & Verification** | Executed 44 automated pytest test cases (unit + integration API tests) achieving 98% overall code coverage and 100% pass rate. |
| **Slide 10** | **Conclusion & Future Scope** | Upgrade baseline heuristic CV models to fine-tuned YOLOv8 and FloodNet U-Net segmenters; add real-time drone telemetry feeds. |

---

## 2. Top Viva / Project Defense Questions & Answers

### Q1: Why did you use HOG + SVM for person detection instead of a deep learning model like YOLOv8?
> **Answer**: Per Section 2.5 of our IEEE SRS specification, the project constraint required a lightweight, dependency-free baseline prototype that runs efficiently on standard CPU hardware without GPU acceleration. HOG + Linear SVM provides fast, reliable pedestrian detection without requiring heavy CUDA runtime dependencies. Section 8 of our SRS documents swapping in fine-tuned YOLOv8 as a drop-in enhancement for production deployment.

### Q2: How does the Decision Support Engine calculate rescue priority?
> **Answer**: The system computes a normalized priority score from 0 to 100 using a multi-factor weighted linear model:
> $$\text{Score} = 0.35 \times (\text{Flood \%}) + 0.45 \times (\text{Victim Score}) + 0.20 \times (\text{Damage \%})$$
> Human presence is weighted highest (45%) to prioritize saving lives, followed by flood inundation (35%) and structural damage (20%). Scores are classified into Low, Medium, High, and Critical risk tiers.

### Q3: How did you verify the reliability of the software system?
> **Answer**: We conducted comprehensive unit and integration testing using `pytest` and `FastAPI TestClient`. We executed **44 test cases** covering CV edge cases (flat images, high-contrast flood scenes, zero-person scenes), decision support boundary conditions, and end-to-end REST API HTTP workflows, achieving **98% statement coverage** with 100% pass rate.

### Q4: How are spatial data and images stored?
> **Answer**: Original and annotated images are persisted on disk under `uploads/` and `annotated/` with UUID-based unique filenames. Analytical metrics (water ratio, victim count, damage score, priority score, risk category, timestamps) are indexed in a relational SQLite database (`database.py`).
