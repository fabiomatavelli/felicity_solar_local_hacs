"""Tests for battery profile matching and field parsing/scaling."""

from __future__ import annotations

from typing import Any

from custom_components.felicity_solar_local.profiles import (
    DEFAULT_PROFILE,
    FLB48314TG1H_PROFILE,
    select_profile,
)


def test_select_profile_matches_flb48314tg1h(sample_response: dict[str, Any]) -> None:
    assert select_profile(sample_response) is FLB48314TG1H_PROFILE


def test_select_profile_falls_back_to_default_for_unknown_model(
    sample_response: dict[str, Any],
) -> None:
    unknown = {**sample_response, "Type": 999, "SubType": 1}
    assert select_profile(unknown) is DEFAULT_PROFILE


def test_parse_scales_verified_fields_correctly(sample_response: dict[str, Any]) -> None:
    data = FLB48314TG1H_PROFILE.parse(sample_response)

    assert data["voltage"] == 54.04
    assert data["current"] == 34.2
    assert data["power"] == round(54.04 * 34.2, 2)
    assert data["soc"] == 96.0
    assert data["soh"] == 100.0
    assert data["capacity"] == 350.0
    assert data["max_cell_voltage"] == 3.38
    assert data["min_cell_voltage"] == 3.376
    assert data["max_cell_number"] == 8
    assert data["min_cell_number"] == 0
    assert data["temperature_1"] == 26.0
    assert data["temperature_2"] == 26.0
    assert data["temperature_3"] == 25.6
    assert data["temperature_4"] == 25.6
    assert data["charge_voltage_limit"] == 57.6
    assert data["discharge_voltage_limit"] == 48.0
    assert data["charge_current_limit"] == 32.0
    assert data["discharge_current_limit"] == 160.0
    assert data["serial_number"] == "075704831426060274"
    assert data["fault"] == 0
    assert data["warning"] == 0


def test_parse_extracts_all_16_cell_voltages(sample_response: dict[str, Any]) -> None:
    data = FLB48314TG1H_PROFILE.parse(sample_response)

    for i in range(16):
        assert data[f"cell_{i + 1}_voltage"] is not None

    assert data["cell_1_voltage"] == 3.376
    assert data["cell_9_voltage"] == 3.38  # matches BMaxMin's reported max


def test_parse_is_null_safe(sample_response: dict[str, Any]) -> None:
    # Batt[2][0] is observed as a JSON null on real hardware; parsing must not crash
    # even though this profile doesn't currently read from the Batt aggregate field.
    assert sample_response["Batt"][2][0] is None
    data = FLB48314TG1H_PROFILE.parse(sample_response)
    assert data["voltage"] is not None


def test_parse_treats_sentinels_as_missing(sample_response: dict[str, Any]) -> None:
    modified = {**sample_response, "BattList": [[54040, 65535], [-1, -1]]}
    data = FLB48314TG1H_PROFILE.parse(modified)
    assert data["current"] is None


def test_default_profile_uses_same_shape(sample_response: dict[str, Any]) -> None:
    data = DEFAULT_PROFILE.parse(sample_response)
    assert data["voltage"] == 54.04
    assert DEFAULT_PROFILE.confidence == "best_effort"
    assert FLB48314TG1H_PROFILE.confidence == "verified"
