"""Run the fictional Salesforce Lead assessment: python -m app.salesforce.demo"""
import json

from .fixtures import summarize_fixture


def main() -> None:
    print(json.dumps(summarize_fixture(), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
