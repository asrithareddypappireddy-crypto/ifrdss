"""
test_detection.py
------------------
Unit tests for the Computer Vision Detection Module (SRS FR-2.1 - FR-2.6).

Uses synthetic images with known, controllable properties (solid colors,
constructed shapes) so expected outcomes can be asserted precisely,
rather than relying on unpredictable real photographs.
"""

import numpy as np
import cv2
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import detection


# ---------------------------------------------------------------------
# detect_flood_water
# ---------------------------------------------------------------------

def test_flood_water_detects_muddy_brown_region():
    """A frame that's entirely a muddy-brown color should be classified
    as mostly flood water."""
    img = np.full((200, 200, 3), (60, 100, 140), dtype=np.uint8)  # BGR muddy brown
    ratio, mask = detection.detect_flood_water(img)
    assert ratio > 0.7, f"Expected high flood ratio on solid muddy image, got {ratio}"
    assert mask.shape == (200, 200)


def test_flood_water_low_on_clear_sky_image():
    """A plain light-blue 'clear sky' color should NOT be classified as
    flood water (it's a bright, low-saturation region, different from
    murky flood water)."""
    img = np.full((200, 200, 3), (235, 220, 210), dtype=np.uint8)  # light BGR (pale)
    ratio, _ = detection.detect_flood_water(img)
    assert ratio < 0.3, f"Expected low flood ratio on pale sky-like image, got {ratio}"


def test_flood_water_ratio_is_bounded():
    """flood_ratio must always be a valid proportion in [0, 1]."""
    rng = np.random.default_rng(42)
    img = rng.integers(0, 255, (150, 150, 3), dtype=np.uint8)
    ratio, mask = detection.detect_flood_water(img)
    assert 0.0 <= ratio <= 1.0
    assert set(np.unique(mask)).issubset({0, 255})


# ---------------------------------------------------------------------
# detect_building_damage
# ---------------------------------------------------------------------

def test_damage_score_low_on_flat_uniform_image():
    """A perfectly flat, uniform-color image has no edges/texture, so the
    damage score should be near zero and the flag should be False."""
    img = np.full((200, 200, 3), (128, 128, 128), dtype=np.uint8)
    score, flag = detection.detect_building_damage(img)
    assert score < 0.15, f"Expected near-zero damage score on flat image, got {score}"
    assert flag is False


def test_damage_score_high_on_chaotic_noise_image():
    """Pure random noise has maximal edge density/high-frequency content,
    which the heuristic should register as a high damage score."""
    rng = np.random.default_rng(7)
    img = rng.integers(0, 255, (200, 200, 3), dtype=np.uint8)
    score, flag = detection.detect_building_damage(img)
    assert score > 0.35, f"Expected high damage score on noisy image, got {score}"
    assert flag is True


def test_damage_score_bounded():
    rng = np.random.default_rng(1)
    img = rng.integers(0, 255, (100, 100, 3), dtype=np.uint8)
    score, _ = detection.detect_building_damage(img)
    assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------
# detect_people
# ---------------------------------------------------------------------

def test_people_detection_returns_consistent_types():
    """On an image with no people, detect_people should still return
    well-typed, consistent results (0 count, empty lists)."""
    img = np.full((300, 300, 3), (200, 200, 200), dtype=np.uint8)
    count, boxes, confidences = detection.detect_people(img)
    assert isinstance(count, int)
    assert count == len(boxes) == len(confidences)
    assert count >= 0


def test_people_detection_handles_small_image():
    """HOG detector requires a minimum window size; the function should
    not crash on a very small image, it should just return zero people."""
    img = np.full((40, 40, 3), (200, 200, 200), dtype=np.uint8)
    count, boxes, confidences = detection.detect_people(img)
    assert count == 0
    assert boxes == []


# ---------------------------------------------------------------------
# annotate_image
# ---------------------------------------------------------------------

def test_annotate_image_preserves_shape():
    img = np.full((150, 150, 3), (100, 100, 100), dtype=np.uint8)
    mask = np.zeros((150, 150), dtype=np.uint8)
    mask[50:100, 50:100] = 255
    annotated = detection.annotate_image(img, boxes=[[10, 10, 30, 30]],
                                          flood_mask=mask, damage_flag=True)
    assert annotated.shape == img.shape
    # image should have changed (overlay/boxes drawn), not be identical to input
    assert not np.array_equal(annotated, img)


# ---------------------------------------------------------------------
# run_detection_pipeline (integration of the three detectors)
# ---------------------------------------------------------------------

def test_full_pipeline_returns_all_expected_keys():
    img = np.full((240, 320, 3), (60, 100, 140), dtype=np.uint8)
    result = detection.run_detection_pipeline(img)
    expected_keys = {
        "person_count", "person_boxes", "person_confidences",
        "flood_ratio", "damage_score", "damage_flag", "annotated_image",
    }
    assert expected_keys.issubset(result.keys())
    assert result["annotated_image"].shape == img.shape


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
