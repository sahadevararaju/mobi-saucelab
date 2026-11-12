
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import (
    Font,
    PatternFill,
    Alignment,
    Border,
    Side,
)
from openpyxl.utils import get_column_letter


# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Excel report location
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
REPORT_FILE = REPORT_DIR / f"Test_execution_report_{REPORT_TIMESTAMP}.xlsx"

SHEET_NAME = "Test Execution Results"

HEADERS = [
    "Test Case ID",
    "Module/Feature",
    "Test Data",
    "Pre-condition",
    "Test Scenario",
    "Test Steps",
    "Expected Result",
    "Environment",
    "Result",
    "Error Message",
]


def _write_headers(sheet):
    for column, header in enumerate(HEADERS, start=1):
        sheet.cell(row=1, column=column, value=header)


def get_workbook():
    """Create a fresh workbook for the current pytest run."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = SHEET_NAME
    _write_headers(sheet)

    return workbook, sheet


def save_test_results(results):
    """
    Write this pytest run's results to the Excel report, replacing any
    previous run's report contents.

    Each item in results must be a dictionary containing
    the fields defined in HEADERS.
    """

    workbook, sheet = get_workbook()

    for result in results:
        row_data = [result.get(header, "") for header in HEADERS]
        sheet.append(row_data)

        row_number = sheet.max_row

        # Format each result row.
        for cell in sheet[row_number]:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )
            cell.border = Border(
                bottom=Side(style="thin", color="D9E2F3")
            )

        # Color the Result cell.
        result_cell = sheet.cell(row=row_number, column=9)
        status = str(result_cell.value).strip().lower()

        if status == "passed":
            result_cell.fill = PatternFill(
                "solid", fgColor="C6EFCE"
            )
            result_cell.font = Font(color="006100")
        elif status == "failed":
            result_cell.fill = PatternFill(
                "solid", fgColor="FFC7CE"
            )
            result_cell.font = Font(color="9C0006")
        elif status == "skipped":
            result_cell.fill = PatternFill(
                "solid", fgColor="FFEB9C"
            )
            result_cell.font = Font(color="9C6500")
        elif status == "not run":
            result_cell.fill = PatternFill(
                "solid", fgColor="D9E1F2"
            )
            result_cell.font = Font(color="404040")

    # Style the header row.
    for cell in sheet[1]:
        cell.font = Font(
            bold=True,
            color="FFFFFF",
        )
        cell.fill = PatternFill(
            "solid",
            fgColor="1F4E78",
        )
        cell.alignment = Alignment(
            vertical="center",
            horizontal="left",
            wrap_text=True,
        )

    # Set readable column widths.
    column_widths = {
        1: 20,
        2: 25,
        3: 35,
        4: 40,
        5: 40,
        6: 60,
        7: 45,
        8: 18,
        9: 14,
        10: 55,
    }

    for column, width in column_widths.items():
        sheet.column_dimensions[
            get_column_letter(column)
        ].width = width

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = (
        f"A1:J{sheet.max_row}"
    )
    sheet.row_dimensions[1].height = 32

    # Enable wrapping for previously existing rows too.
    for row in sheet.iter_rows(
        min_row=2,
        max_row=sheet.max_row,
        min_col=1,
        max_col=10,
    ):
        for cell in row:
            cell.alignment = Alignment(
                vertical="top",
                wrap_text=True,
            )

    workbook.save(REPORT_FILE)
    print(f"\nExcel report generated: {REPORT_FILE}")
