"""
Tests for the data_import module.

Verifies that import functions exist, CSV parsing works correctly,
and the module structure is sound.
"""
import pytest
import csv
import os
import tempfile
import data_import


def test_safe_float_conversions():
    """Verify _safe_float handles edge cases correctly."""
    assert data_import._safe_float("3.14") == 3.14
    assert data_import._safe_float("0") == 0.0
    assert data_import._safe_float("") is None
    assert data_import._safe_float(None) is None
    assert data_import._safe_float("not_a_number") is None


def test_safe_int_conversions():
    """Verify _safe_int handles edge cases correctly."""
    assert data_import._safe_int("42") == 42
    assert data_import._safe_int("3.14") == 3
    assert data_import._safe_int("") is None
    assert data_import._safe_int(None) is None
    assert data_import._safe_int("abc") is None


def test_import_all_data_exists():
    """Verify the main import function is importable."""
    assert callable(data_import.import_all_data)


def test_csv_dict_reader_parsing(tmp_path):
    """
    Verify that csv.DictReader (used instead of pandas) correctly parses
    a minimal CSV in the expected format.
    """
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "fdc_id,food_name,food_category,data_type,brand_name,brand_owner,"
        "calories,protein_g,fat_g,carbs_g,sodium_mg,health_score\n"
        "9999,Test Food,Snacks,SR Legacy,TestBrand,TestCorp,"
        "100,5.0,2.0,20.0,50.0,75.0\n"
    )

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["fdc_id"] == "9999"
    assert rows[0]["food_name"] == "Test Food"
    assert rows[0]["calories"] == "100"
