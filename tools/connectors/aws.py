import json
from datetime import date
from pathlib import Path

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from .base import BaseConnector, ConnectorResult


class AWSConnector(BaseConnector):
    name = "AWS"
    stable = True

    def is_configured(self) -> bool:
        return self._is_set("access_key_id", "secret_access_key", "account_id")

    def download(self, start: date, end: date, out_dir: Path) -> ConnectorResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        period = start.strftime("%Y-%m")
        filename = out_dir / f"AWS_{period}.json"

        if filename.exists():
            return ConnectorResult(connector=self.name, files=[], count=0, skipped=1, error=None, hint=None)

        # Calculate first day of next month for end of range
        if start.month == 12:
            end_str = f"{start.year + 1}-01-01"
        else:
            end_str = f"{start.year}-{start.month + 1:02d}-01"

        try:
            ce = boto3.client(
                "ce",
                aws_access_key_id=self.config["access_key_id"],
                aws_secret_access_key=self.config["secret_access_key"],
                region_name="us-east-1",
            )
            response = ce.get_cost_and_usage(
                TimePeriod={"Start": start.strftime("%Y-%m-%d"), "End": end_str},
                Granularity="MONTHLY",
                Metrics=["BlendedCost", "UnblendedCost", "UsageQuantity"],
            )
            filename.write_text(json.dumps(response, indent=2, default=str))
            return ConnectorResult(connector=self.name, files=[filename], count=1, skipped=0, error=None, hint=None)

        except ClientError as e:
            code = e.response["Error"]["Code"]
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error=f"AWS error: {code}",
                hint=f"Check access_key_id and IAM permissions (ce:GetCostAndUsage) in config.yml",
            )
        except NoCredentialsError:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error="AWS credentials not found",
                hint="Check access_key_id and secret_access_key in ~/.invoicepilot/config.yml",
            )
        except Exception as e:
            return ConnectorResult(
                connector=self.name, files=[], count=0, skipped=0,
                error=str(e), hint=None,
            )
