"""Opt-in dev-org read-only preview, printing aggregate counts only.

Environment: SIGNALDESK_SF_INSTANCE_URL, SIGNALDESK_SF_ACCESS_TOKEN
Do not commit or share tokens. Use synthetic Lead records in a dev org only.
"""
import json
from .reader import SalesforceReadConfig, SalesforceReadError, preview_salesforce_leads


def main():
    try:
        result = preview_salesforce_leads(SalesforceReadConfig.from_environment())
    except SalesforceReadError as exc:
        print(json.dumps({"status": "hold", "error": str(exc)}))
        return 1
    print(json.dumps(result.summary(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
