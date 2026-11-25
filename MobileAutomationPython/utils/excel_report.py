
from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.chart import PieChart, Reference
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.chart.series import DataPoint
from openpyxl.chart.shapes import GraphicalProperties
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
RESULTS_CHART_SHEET_NAME = "Results Chart"


def get_device_details(capabilities):
    """Return readable device and OS values from Appium capabilities."""

    capabilities = capabilities or {}

    def value_for(*names):
        return next(
            (
                str(capabilities[name]).strip()
                for name in names
                if capabilities.get(name) not in (None, "")
            ),
            "",
        )

    device = value_for(
        # Appium/Sauce Labs exposes the user-facing product name separately
        # from modelNumber/deviceModel (for example, Galaxy S23 FE vs SM-S711B).
        "name",
        "appium:name",
        "deviceName",
        "appium:deviceName",
        "device",
        "deviceModel",
        "appium:deviceModel",
        "modelNumber",
        "appium:modelNumber",
        "model",
    )
    platform = value_for("appium:platformName", "platformName")
    version = value_for(
        "appium:platformVersion",
        "platformVersion",
        "os_version",
    )
    return device, " ".join(part for part in (platform, version) if part)

HEADERS = [
    "Test Case ID",
    "Module/Feature",
    "Test Data",
    "Pre-condition",
    "Test Scenario",
    "Test Steps",
    "Expected Result",
    "Environment",
    "Device",
    "OS",
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
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.tabColor = "5B9BD5"
    _write_headers(sheet)
    _add_results_chart_sheet(workbook)

    return workbook, sheet


def _add_results_chart_sheet(workbook):
    """Add a formula-driven outcome dashboard before the detail sheet."""

    sheet = workbook.create_sheet(RESULTS_CHART_SHEET_NAME, index=0)
    sheet.sheet_view.showGridLines = False
    sheet.sheet_properties.tabColor = "1F4E78"

    result_column = get_column_letter(HEADERS.index("Result") + 1)
    id_column = get_column_letter(HEADERS.index("Test Case ID") + 1)
    result_range = f"'{SHEET_NAME}'!${result_column}:${result_column}"
    id_range = f"'{SHEET_NAME}'!${id_column}:${id_column}"

    sheet["A1"] = "Test Execution Results"
    sheet["A1"].font = Font(name="Aptos Display", size=18, bold=True, color="17365D")
    sheet["A2"] = f"Run summary  |  Generated {REPORT_TIMESTAMP}"
    sheet["A2"].font = Font(name="Aptos", size=10, italic=True, color="64748B")

    kpis = (
        ("A4", "Total Test Cases", "A5", f"=MAX(0,COUNTA({id_range})-1)", "17365D"),
        ("C4", "Executed", "C5", "=SUM(B12:B13)", "2563EB"),
        ("E4", "Passed", "E5", "=B12", "15803D"),
        ("G4", "Failed", "G5", "=B13", "B91C1C"),
        ("A7", "Skipped", "A8", "=B14", "A16207"),
        ("C7", "Not Run", "C8", "=B15", "64748B"),
        ("E7", "Execution Rate", "E8", "=IFERROR(C5/A5,0)", "2563EB"),
        ("G7", "Pass Rate", "G8", "=IFERROR(E5/C5,0)", "15803D"),
    )
    for label_cell, label, value_cell, formula, accent in kpis:
        sheet[label_cell] = label
        sheet[label_cell].font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        sheet[label_cell].fill = PatternFill("solid", fgColor=accent)
        sheet[label_cell].alignment = Alignment(horizontal="center", vertical="center")
        sheet[value_cell] = formula
        sheet[value_cell].font = Font(name="Aptos Display", size=18, bold=True, color=accent)
        sheet[value_cell].fill = PatternFill("solid", fgColor="F1F5F9")
        sheet[value_cell].alignment = Alignment(horizontal="center", vertical="center")

    sheet["E8"].number_format = "0%"
    sheet["G8"].number_format = "0%"

    table_headers = ("Outcome", "Test Cases", "Share of Total")
    for column, value in enumerate(table_headers, start=1):
        cell = sheet.cell(row=11, column=column, value=value)
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F4E78")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    status_rows = (
        (12, "Passed", "15803D", f'=COUNTIF({result_range},"Passed")'),
        (13, "Failed", "B91C1C", f'=COUNTIF({result_range},"Failed")'),
        (14, "Skipped", "A16207", f'=COUNTIF({result_range},"Skipped")'),
        (15, "Not Run", "64748B", f'=COUNTIF({result_range},"Not Run")'),
        (16, "Other", "475569", "=MAX(0,$A$5-SUM(B12:B15))"),
    )
    for row, label, color, formula in status_rows:
        sheet.cell(row=row, column=1, value=label)
        sheet.cell(row=row, column=2, value=formula)
        sheet.cell(row=row, column=3, value=f"=IFERROR(B{row}/$A$5,0)")
        sheet.cell(row=row, column=1).font = Font(name="Aptos", size=10, bold=True, color=color)
        for column in range(1, 4):
            cell = sheet.cell(row=row, column=column)
            cell.fill = PatternFill("solid", fgColor="F8FAFC" if row % 2 == 0 else "FFFFFF")
            cell.border = Border(bottom=Side(style="thin", color="D9E2F3"))
            cell.alignment = Alignment(vertical="center")
        sheet.cell(row=row, column=2).number_format = "0"
        sheet.cell(row=row, column=3).number_format = "0%"

    palette = ("16A34A", "DC2626", "F59E0B", "64748B", "CBD5E1")
    pie = PieChart()
    pie.title = "Test Case Outcomes"
    pie.style = 10
    pie.height = 8
    pie.width = 13
    # Reserve space above the plot so the title does not sit on top of the pie.
    pie.layout = Layout(manualLayout=ManualLayout(y=0.14, h=0.78))
    pie.add_data(Reference(sheet, min_col=2, min_row=11, max_row=16), titles_from_data=True)
    pie.set_categories(Reference(sheet, min_col=1, min_row=12, max_row=16))
    pie.series[0].data_points = [
        DataPoint(idx=index, spPr=GraphicalProperties(solidFill=color))
        for index, color in enumerate(palette)
    ]
    # Keep labels out of the pie: Excel positions labels for zero and small
    # slices unpredictably, which makes them overlap the title and each other.
    # The adjacent outcome table already shows each count and percentage.
    # Leave labels unset; some Excel renderers display category labels even
    # when each DataLabelList flag is explicitly false.
    pie.dataLabels = None
    pie.legend.position = "r"
    sheet.add_chart(pie, "D11")

    for column, width in {"A": 22, "B": 16, "C": 20, "D": 3, "E": 16, "F": 3, "G": 16, "H": 3}.items():
        sheet.column_dimensions[column].width = width
    for row in (4, 7):
        sheet.row_dimensions[row].height = 24
    for row in (5, 8):
        sheet.row_dimensions[row].height = 32
    sheet.row_dimensions[11].height = 24
    for row in range(12, 17):
        sheet.row_dimensions[row].height = 22

    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 1
    workbook.calculation.fullCalcOnLoad = True
    workbook.calculation.forceFullCalc = True
    workbook.calculation.calcMode = "auto"


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

    # Style the header row.
    for cell in sheet[1]:
        cell.font = Font(
            name="Aptos",
            bold=True,
            color="FFFFFF",
        )
        cell.fill = PatternFill(
            "solid",
            fgColor="1F4E78",
        )
        cell.alignment = Alignment(
            vertical="center",
            horizontal="center",
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
        9: 24,
        10: 20,
        11: 14,
        12: 55,
    }

    for column, width in column_widths.items():
        sheet.column_dimensions[
            get_column_letter(column)
        ].width = width

    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = (
        f"A1:{get_column_letter(len(HEADERS))}{sheet.max_row}"
    )
    sheet.row_dimensions[1].height = 32

    # Add restrained banding, readable spacing, and clear status emphasis.
    centered_columns = {
        HEADERS.index(header) + 1
        for header in ("Test Case ID", "Environment", "Device", "OS", "Result")
    }
    widths_by_column = {
        column: column_widths[column]
        for column in range(1, len(HEADERS) + 1)
    }
    result_column = HEADERS.index("Result") + 1
    status_styles = {
        "passed": ("C6EFCE", "006100"),
        "failed": ("FFC7CE", "9C0006"),
        "skipped": ("FFEB9C", "9C6500"),
        "not run": ("D9E1F2", "404040"),
    }
    for row_number in range(2, sheet.max_row + 1):
        row_fill = "F2F7FC" if row_number % 2 == 0 else "FFFFFF"
        line_count = 1
        for column, cell in enumerate(sheet[row_number], start=1):
            cell.fill = PatternFill("solid", fgColor=row_fill)
            cell.font = Font(name="Aptos", size=10, color="243447")
            cell.alignment = Alignment(
                vertical="center",
                horizontal="center" if column in centered_columns else "left",
                wrap_text=True,
            )
            cell.border = Border(
                bottom=Side(style="thin", color="D9E5F2")
            )
            value = "" if cell.value is None else str(cell.value)
            width = widths_by_column[column]
            line_count = max(
                line_count,
                sum(
                    max(1, (len(part) + width - 1) // width)
                    for part in (value.splitlines() or [""])
                ),
            )

        id_cell = sheet.cell(row=row_number, column=1)
        id_cell.font = Font(name="Aptos", size=10, bold=True, color="1F4E78")

        result_cell = sheet.cell(row=row_number, column=result_column)
        status_style = status_styles.get(str(result_cell.value).strip().lower())
        if status_style:
            fill_color, font_color = status_style
            result_cell.fill = PatternFill("solid", fgColor=fill_color)
            result_cell.font = Font(name="Aptos", size=10, bold=True, color=font_color)

        sheet.row_dimensions[row_number].height = min(
            120,
            max(32, line_count * 15 + 8),
        )

    workbook.save(REPORT_FILE)
    print(f"\nExcel report generated: {REPORT_FILE}")
