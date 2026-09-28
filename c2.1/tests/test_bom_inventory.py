"""Reported donor and stop-button inventory is not qualified stock."""
import csv
import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]


def csv_rows(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class InventoryCostTests(unittest.TestCase):
    def test_historical_owned_lines_are_not_free_current_parts(self):
        historical = {row["item_id"] for row in csv_rows(REPO / "c2/bom/cost_ledger.csv")
                      if row["owned_verified"] == "True"}
        active = {row["part_id"]: row for row in csv_rows(
            REPO / "c2.1/bom/system_bom.csv")}
        reclassified = (historical & active.keys()) - {"SAFE-STOP", "EL-PSU"}
        self.assertEqual(len(reclassified), 9)
        for part_id in reclassified:
            row = active[part_id]
            self.assertEqual(row["landed_line_KRW"], "", part_id)
            self.assertEqual(row["cost_state"], "UNQUOTED_NOT_ZERO", part_id)
            self.assertEqual(row["status"],
                             "DONOR_CUT_FIT_OR_PROCUREMENT_HOLD"
                             if part_id.startswith("FR-") else "PROCUREMENT_HOLD",
                             part_id)
        stop = active["SAFE-STOP"]
        self.assertEqual(stop["landed_line_KRW"], "")
        self.assertEqual(stop["status"], "OWNED_REPORTED_RATING_HOLD")
        self.assertEqual(stop["cost_state"], "OWNED_BUTTON_NO_NEW_PURCHASE_UNQUALIFIED")
        psu = active["EL-PSU"]
        self.assertEqual(psu["landed_line_KRW"], "")
        self.assertEqual(psu["status"], "OWNED_REPORTED_RATING_HOLD")
        self.assertEqual(psu["cost_state"], "OWNED_DONOR_PSU_NO_NEW_PURCHASE_UNQUALIFIED")
        self.assertFalse(any(row["cost_state"] == "OWNED_NO_NEW_PURCHASE"
                             or row["landed_line_KRW"] == "0"
                             for row in active.values()))
        summary = json.loads((REPO / "c2.1/results/system_bom_summary.json").read_text())
        self.assertEqual(summary["current_inventory"]["reported_owned_button_rows"], 1)
        self.assertEqual(summary["current_inventory"]["reported_owned_psu_rows"], 1)
        self.assertEqual(summary["current_inventory"]["donor_printer"]["other_subparts"],
                         "UNALLOCATED_PENDING_LABEL_AND_DIMENSIONS")
        self.assertEqual(summary["current_inventory"]["qualified_stock_rows"], 0)
        self.assertEqual(summary["current_inventory"]["historical_owned_rows_reclassified"],
                         len(reclassified))
        self.assertEqual(summary["unknown_cost_rows"], len(active))
        self.assertIsNone(summary["known_landed_total_KRW"])
        self.assertGreater(summary["candidate_motor_budget_gap_KRW"], 0)
        self.assertIsNone(summary["profile_cut_plan"]["stock_available"])
        self.assertTrue(summary["profile_cut_plan"]["stock_conservation_passed"])
        self.assertEqual(summary["procurement"], "HOLD")


if __name__ == "__main__":
    unittest.main()
