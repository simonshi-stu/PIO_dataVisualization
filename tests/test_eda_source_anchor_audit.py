from __future__ import annotations

import unittest

import pandas as pd

from backend.app.main import (
    WorkbookSession,
    _build_eda_source_anchor_audit,
    _filter_forecast_sources,
    _forecast_cutoff_context,
    _forecast_sales_sheet_name,
)
from pio_platform.data_loader import DatasetBundle


class EdaSourceAnchorAuditTests(unittest.TestCase):
    def test_source_h_models_show_governed_anchor_years_and_latest_quantity(self) -> None:
        source = pd.DataFrame(
            {
                "PIS_CMP_KND": ["H", "H", "K"],
                "Model": ["G70", "Sportage", "Sportage"],
                "PIS_MDL_YY": [2026, 2027, 2027],
                "SumOfPIS_INST_QT": [10, 20, 30],
                "SumOfPIS_CRP_CFM_PRI": [500, 900, 1400],
            }
        )
        dates = pd.Series(pd.to_datetime(["2026-07-10", "2026-07-20", "2026-07-20"]))
        facts = pd.DataFrame(
            {
                "brand": ["H", "H", "K"],
                "modelName": ["G70", "Sportage", "Sportage"],
                "anchorBrand": ["GMA", "KUS", "KUS"],
                "anchorMappingMethod": [
                    "dealer_wholesale_exact",
                    "dealer_wholesale_exact",
                    "dealer_wholesale_exact",
                ],
            }
        )
        columns = {
            "brand": "PIS_CMP_KND",
            "model": "Model",
            "model_year": "PIS_MDL_YY",
        }
        payload = _build_eda_source_anchor_audit(
            source,
            columns,
            dates,
            pd.to_numeric(source["SumOfPIS_CRP_CFM_PRI"]),
            pd.to_numeric(source["SumOfPIS_INST_QT"]),
            facts,
        )

        self.assertEqual(payload["latestMonth"], "2026-07")
        source_h = {
            (record["anchorBrand"], record["modelName"]): record
            for record in payload["sourceHModels"]
        }
        self.assertEqual(source_h[("GMA", "G70")]["modelYears"], ["2026"])
        self.assertEqual(source_h[("KUS", "Sportage")]["latestMonthQuantity"], 20.0)
        summary = {
            (record["sourceCode"], record["anchorBrand"]): record["pioQuantity"]
            for record in payload["summary"]
        }
        self.assertEqual(summary[("H", "KUS")], 20)
        self.assertEqual(summary[("K", "KUS")], 30)

    def test_forecast_source_is_governed_pio_sheet_not_active_workspace_sheet(self) -> None:
        session = WorkbookSession(
            workbook_id="test",
            filename="test.xlsx",
            file_bytes=b"",
            sheet_names=["Vehicle_Wholesale_Data", "PIO_Sales_Data", "Working_Days"],
        )

        self.assertEqual(
            _forecast_sales_sheet_name(session, "Vehicle_Wholesale_Data"),
            "PIO_Sales_Data",
        )

    def test_anchor_filters_do_not_reuse_unreliable_source_h_k_codes(self) -> None:
        facts = pd.DataFrame(
            {
                "brand": ["H", "H", "K"],
                "anchorBrand": ["GMA", "KUS", "KUS"],
                "modelName": ["G70", "Sportage", "Sportage"],
                "partNumber": ["A", "B", "C"],
                "plc": ["Mat", "Mat", "Tray"],
                "month": ["2026-06", "2026-06", "2026-06"],
            }
        )
        wholesale = pd.DataFrame(
            {
                "anchorBrand": ["HMA", "GMA", "KUS"],
                "modelName": ["Elantra", "G70", "Sportage"],
                "month": ["2026-06", "2026-06", "2026-06"],
            }
        )

        anchor_facts, anchor_wholesale = _filter_forecast_sources(
            facts,
            wholesale,
            brand=["GMA"],
            model=[],
            part=[],
            start_date="",
            end_date="",
        )
        self.assertEqual(set(anchor_facts["anchorBrand"]), {"GMA"})
        self.assertEqual(set(anchor_wholesale["anchorBrand"]), {"GMA"})

        source_facts, source_wholesale = _filter_forecast_sources(
            facts,
            wholesale,
            brand=["H"],
            model=[],
            part=[],
            start_date="",
            end_date="",
        )
        self.assertEqual(set(source_facts["anchorBrand"]), {"GMA", "KUS"})
        self.assertEqual(set(source_wholesale["anchorBrand"]), {"GMA", "KUS"})

    def test_historical_end_filter_is_treated_as_a_complete_month(self) -> None:
        dates = pd.Series(pd.to_datetime(["2023-01-01", "2026-07-22"]))
        bundle = DatasetBundle(
            dataframe=pd.DataFrame({"Date": dates}),
            profile={},
            roles={"date": "Date"},
            date_candidates={"Date": dates},
            numeric_fields=[],
            categorical_fields=[],
            date_fields=["Date"],
        )
        session = WorkbookSession(
            workbook_id="test",
            filename="test.xlsx",
            file_bytes=b"",
            sheet_names=["PIO_Sales_Data"],
            bundles={"PIO_Sales_Data": bundle},
        )

        is_complete, latest_date = _forecast_cutoff_context(
            session,
            "PIO_Sales_Data",
            "2025-12-31",
        )

        self.assertTrue(is_complete)
        self.assertEqual(latest_date, pd.Timestamp("2025-12-31"))


if __name__ == "__main__":
    unittest.main()
