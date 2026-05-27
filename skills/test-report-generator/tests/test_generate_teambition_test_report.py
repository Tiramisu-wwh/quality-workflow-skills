import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_teambition_test_report.py"
SPEC = importlib.util.spec_from_file_location("generate_teambition_test_report", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class TBClientHeadersTest(unittest.TestCase):
    def test_authorization_header_uses_bearer_prefix(self) -> None:
        client = MODULE.TBClient.__new__(MODULE.TBClient)
        client.auth = {
            "TEAMBITION_TENANT_ID": "tenant-id",
            "TEAMBITION_TENANT_TYPE": "organization",
            "TEAMBITION_OPERATOR_ID": "operator-id",
        }
        client.token = "sample-token"

        headers = client.headers()

        self.assertEqual(headers["Authorization"], "Bearer sample-token")


if __name__ == "__main__":
    unittest.main()
