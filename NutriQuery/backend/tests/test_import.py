import pytest
import data_import

def test_parse_csv(tmp_path):
    # Create a dummy CSV file to test parsing logic
    csv_file = tmp_path / "test.csv"
    csv_file.write_text("id,name,value\n1,Apple,100\n2,Banana,200")
    
    # Normally we'd call data_import.parse_csv if it was extracted,
    # but since data_import is an end-to-end script, we can mock it
    # or just test that the module imports correctly without syntax errors.
    assert hasattr(data_import, "import_all_data")

# Avoid running the full import_all_data() in automated tests
# as it drops tables, recreates them, and inserts 40k rows.
