import re

from openpyxl import load_workbook

from utils import excel_report


def test_report_filename_includes_timestamp():
    assert re.fullmatch(
        r"Test_execution_report_\d{8}_\d{6}_\d{3}\.xlsx",
        excel_report.REPORT_FILE.name,
    )


def test_empty_results_generate_workbook_with_headers(tmp_path, monkeypatch):
    report_dir = tmp_path / "reports"
    report_file = report_dir / "report.xlsx"
    monkeypatch.setattr(excel_report, "REPORT_DIR", report_dir)
    monkeypatch.setattr(excel_report, "REPORT_FILE", report_file)

    excel_report.save_test_results([])

    workbook = load_workbook(report_file, data_only=True)
    sheet = workbook[excel_report.SHEET_NAME]
    assert [
        sheet.cell(row=1, column=column).value
        for column in range(1, len(excel_report.HEADERS) + 1)
    ] == excel_report.HEADERS
    assert sheet.max_row == 1
    workbook.close()


def test_each_run_replaces_prior_results_in_single_workbook(
    tmp_path, monkeypatch
):
    report_dir = tmp_path / "reports"
    report_dir.mkdir()
    report_file = report_dir / "report.xlsx"
    monkeypatch.setattr(excel_report, "REPORT_DIR", report_dir)
    monkeypatch.setattr(excel_report, "REPORT_FILE", report_file)

    first_result = {header: "" for header in excel_report.HEADERS}
    first_result.update({"Test Case ID": "TC001", "Result": "Failed"})
    excel_report.save_test_results([first_result])

    second_result = {header: "" for header in excel_report.HEADERS}
    second_result.update({"Test Case ID": "TC002", "Result": "Passed"})
    excel_report.save_test_results([second_result])

    saved_workbook = load_workbook(report_file, data_only=True)
    sheet = saved_workbook[excel_report.SHEET_NAME]

    assert saved_workbook.sheetnames == [excel_report.SHEET_NAME]
    assert sheet.max_row == 2
    assert sheet["A2"].value == "TC002"
    assert sheet["I2"].value == "Passed"
    assert len(list(report_dir.glob("*.xlsx"))) == 1
