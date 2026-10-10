"""
detection.py
------------
Computer Vision Detection Module for IFRDSS.

Implements the three detection capabilities called for in the SRS
(FR-2.1 - FR-2.6):
  1. Person detection            -> uses OpenCV's pretrained HOG + SVM
                                     people detector (real, trained model).
  2. Flooded-road / water extent -> color/texture heuristic over HSV space
                                     (baseline CV technique; designed to be
                                     swapped for a trained U-Net/YOLO
                                     segmentation model in a future
                                     iteration, per SRS Section 8).
  3. Building-damage indicator   -> edge-chaos / texture-irregularity
                                     heuristic (baseline proxy for a
                                     trained damage-classification model).

Each function returns plain, JSON-serializable data plus draws an
annotated copy of the image (bounding boxes / overlays) so the frontend
can show the user exactly what was detected.
"""

import cv2
import numpy as np


# A single shared HOG descriptor initialised once at import time.
if hasattr(cv2, "HOGDescriptor"):
    _hog = cv2.HOGDescriptor()
    _hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
elif hasattr(cv2, "objdetect") and hasattr(cv2.objdetect, "HOGDescriptor"):
    _hog = cv2.objdetect.HOGDescriptor()
    _hog.setSVMDetector(cv2.objdetect.HOGDescriptor_getDefaultPeopleDetector())
else:
    _hog = None


def detect_people(image_bgr: np.ndarray):
    """Detect people in the image using HOG + SVM, augmented with
    upper-body / torso cascades for flood victims with submerged lower bodies.

    Returns:
        count (int), boxes (list of [x, y, w, h]), confidences (list[float])
    """
    h, w = image_bgr.shape[:2]
    if h < 48 or w < 48:
        return 0, [], []

    scale = 640.0 / max(h, w) if max(h, w) > 640 else 1.0
    resized = cv2.resize(image_bgr, (int(w * scale), int(h * scale)))
    rh, rw = resized.shape[:2]

    boxes = []
    confidences = []

    # 1. HOG Pedestrian Detector (with finer 4x4 stride)
    if _hog is not None and rh >= 64 and rw >= 64:
        try:
            rects, weights = _hog.detectMultiScale(
                resized, winStride=(4, 4), padding=(4, 4), scale=1.05
            )
            for (x, y, bw, bh), conf in zip(rects, weights):
                boxes.append([int(x / scale), int(y / scale), int(bw / scale), int(bh / scale)])
                confidences.append(float(conf))
        except cv2.error:
            pass

    # 2. Upper-Body Cascade (vital for flood scenes where legs are submerged under water)
    try:
        import os
        upper_path = os.path.join(cv2.data.haarcascades, "haarcascade_upperbody.xml")
        if os.path.exists(upper_path):
            cascade = cv2.CascadeClassifier(upper_path)
            gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
            uppers = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=2, minSize=(25, 35))
            for (x, y, bw, bh) in uppers:
                boxes.append([int(x / scale), int(y / scale), int(bw / scale), int(bh / scale)])
                confidences.append(0.6)
    except Exception:
        pass

    # 3. Non-Maximum Suppression to eliminate duplicate overlapping detections
    if len(boxes) > 0:
        indices = cv2.dnn.NMSBoxes(boxes, confidences, score_threshold=0.0, nms_threshold=0.4)
        if len(indices) > 0:
            final_boxes = [boxes[i] for i in indices.flatten()]
            final_confs = [confidences[i] for i in indices.flatten()]
        else:
            final_boxes = boxes
            final_confs = confidences
    else:
        final_boxes = []
        final_confs = []

    return len(final_boxes), final_boxes, final_confs


def detect_flood_water(image_bgr: np.ndarray):
    """Estimate flood-water coverage using an HSV color-range heuristic.

    Flood/muddy water tends to fall in a fairly desaturated, brown-grey-to
    -murky-blue HSV band. This is a lightweight baseline detector (not a
    trained segmentation network) intended to approximate flooded-road
    extent for demonstration purposes.

    Returns:
        flood_ratio (float 0-1), mask (np.ndarray uint8 0/255)
    """
    hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

    # Muddy/brown flood water
    lower_brown = np.array([5, 20, 20])
    upper_brown = np.array([30, 180, 200])
    mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)

    # Murky blue-grey water
    lower_blue = np.array([80, 10, 40])
    upper_blue = np.array([140, 120, 200])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)

    mask = cv2.bitwise_or(mask_brown, mask_blue)

    # Morphological clean-up to remove speckle noise
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    flood_ratio = float(np.count_nonzero(mask)) / float(mask.size)
    return flood_ratio, mask


def detect_building_damage(image_bgr: np.ndarray):
    """Estimate a 'structural irregularity' score as a proxy for visible
    building/road damage (rubble, collapsed structures, debris).

    Uses edge density + Laplacian variance: damaged/rubble scenes tend to
    have chaotic, high-frequency edge patterns compared to intact
    buildings or clear roads.

    Returns:
        damage_score (float 0-1), damage_flag (bool)
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    edge_density = float(np.count_nonzero(edges)) / float(edges.size)

    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    # normalize laplacian variance into a 0-1-ish range empirically
    norm_lap = min(laplacian_var / 1500.0, 1.0)

    damage_score = float(min(1.0, 0.6 * edge_density * 10 + 0.4 * norm_lap))
    damage_flag = damage_score > 0.35
    return damage_score, damage_flag


def annotate_image(image_bgr: np.ndarray, boxes, flood_mask, damage_flag):
    """Draw bounding boxes for people + a translucent flood overlay onto a
    copy of the image, and return it for saving/display."""
    annotated = image_bgr.copy()

    # Flood overlay (semi-transparent red tint over detected water)
    overlay = annotated.copy()
    overlay[flood_mask > 0] = (0, 0, 255)
    annotated = cv2.addWeighted(overlay, 0.35, annotated, 0.65, 0)

    # Person bounding boxes (green) + Privacy Anonymization Blur (Head/Face Region)
    for (x, y, w, h) in boxes:
        # Apply Gaussian Blur on head region (upper 35% of box) for legal privacy compliance
        head_h = max(1, int(h * 0.35))
        roi = annotated[y:y+head_h, x:x+w]
        if roi.size > 0 and roi.shape[0] > 0 and roi.shape[1] > 0:
            ksize = (max(3, (w // 3) | 1), max(3, (head_h // 3) | 1))
            blurred_roi = cv2.GaussianBlur(roi, ksize, 30)
            annotated[y:y+head_h, x:x+w] = blurred_roi

        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(annotated, "person [anonymized]", (x, max(0, y - 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Damage banner
    if damage_flag:
        cv2.putText(annotated, "DAMAGE INDICATORS DETECTED", (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    return annotated


def run_detection_pipeline(image_bgr: np.ndarray):
    """Run all detectors and return a single structured result dict."""
    person_count, boxes, confidences = detect_people(image_bgr)
    flood_ratio, flood_mask = detect_flood_water(image_bgr)
    damage_score, damage_flag = detect_building_damage(image_bgr)

    annotated = annotate_image(image_bgr, boxes, flood_mask, damage_flag)

    return {
        "person_count": person_count,
        "person_boxes": boxes,
        "person_confidences": confidences,
        "flood_ratio": round(flood_ratio, 4),
        "damage_score": round(damage_score, 4),
        "damage_flag": damage_flag,
        "annotated_image": annotated,
    }
