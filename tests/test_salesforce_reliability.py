"""Offline regression tests for safe configuration and complete query results."""
import json
import unittest
from unittest.mock import Mock, patch
from app.salesforce.reader import (
    SalesforceReadConfig, SalesforceReadError, preview_salesforce_leads,
)


class SalesforceReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.config = SalesforceReadConfig(
            "https://sandbox.my.salesforce.com", "SYNTHETIC_SECRET"
        )

    def test_config_representation_excludes_token(self):
        self.assertNotIn("SYNTHETIC_SECRET", repr(self.config))
        self.assertNotIn("SYNTHETIC_SECRET", str(self.config))
        self.assertEqual(self.config.access_token, "SYNTHETIC_SECRET")

    def read(self, payload):
        response = Mock()
        response.status = 200
        response.read.return_value = json.dumps(payload).encode()
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        return opener

    def test_invalid_totals_rejected_before_classification_without_retry(self):
        for total in (None, True, False, "1", 1.0, -1, 0, 2):
            with self.subTest(total=total):
                payload = {"done": True, "records": [{}], "totalSize": total}
                opener = self.read(payload)
                with patch("app.salesforce.reader.assess_synthetic_lead") as assess:
                    with self.assertRaises(SalesforceReadError):
                        preview_salesforce_leads(self.config, opener=opener)
                    assess.assert_not_called()
                opener.open.assert_called_once()

    def test_missing_total_rejected(self):
        opener = self.read({"done": True, "records": []})
        with self.assertRaises(SalesforceReadError):
            preview_salesforce_leads(self.config, opener=opener)

    def test_matching_totals_allow_empty_and_nonempty_results(self):
        for records in ([], [{}]):
            with self.subTest(records=records):
                opener = self.read(
                    {"done": True, "records": records, "totalSize": len(records)}
                )
                result = preview_salesforce_leads(self.config, opener=opener)
                self.assertEqual(result.summary()["records_assessed"], len(records))
                self.assertEqual(result.summary()["crm_writes"], 0)
                opener.open.assert_called_once()
