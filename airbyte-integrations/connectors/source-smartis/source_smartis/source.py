import logging
from typing import Any, List, Mapping, Tuple, Optional

from airbyte_cdk.sources import AbstractSource
from airbyte_protocol.models import SyncMode

from .auth import CredentialsCraftAuthenticator, TokenAuthenticator
from .utils import get_config_date_range
from .streams.base import SmartisStream
from .streams.projects import Projects
from .streams.metrics import Metrics
from .streams.groupings import Groupings
from .streams.reports import Reports
from .streams.attributions import Attributions


class SourceSmartis(AbstractSource):
    """
    Smartis source
    API docs: https://my.smartis.bi/api/documentation
    """

    def check_connection(
        self, logger: logging.Logger, config: Mapping[str, Any]
    ) -> Tuple[bool, Optional[Any]]:
        try:
            auth = self.get_auth(config)
            projects_stream = Projects(authenticator=auth)
            next(projects_stream.read_records(sync_mode=SyncMode.full_refresh))
            return True, None
        except Exception as e:
            return False, e

    @staticmethod
    def get_auth(config: Mapping[str, Any]) -> TokenAuthenticator:
        auth_type: str = config["credentials"]["auth_type"]
        if auth_type == "access_token_auth":
            return TokenAuthenticator(config["credentials"]["access_token"])
        elif auth_type == "credentials_craft_auth":
            return CredentialsCraftAuthenticator(
                credentials_craft_host=config["credentials"]["credentials_craft_host"],
                credentials_craft_token=config["credentials"][
                    "credentials_craft_token"
                ],
                credentials_craft_token_id=config["credentials"][
                    "credentials_craft_token_id"
                ],
            )
        else:
            raise Exception(
                f"Invalid Auth type {auth_type}. Available: access_token_auth and credentials_craft_auth",
            )

    def streams(self, config: Mapping[str, Any]) -> List[SmartisStream]:
        start_date, end_date = get_config_date_range(config)
        auth = self.get_auth(config)

        projects_stream = Projects(authenticator=auth)

        metrics_stream = Metrics(authenticator=auth)

        group_by_metrics: dict[str, any] = config["group_by_metrics"]
        if group_by_metrics["group_by_metric_type"] == "metrics":
            groupings_stream = Groupings(
                authenticator=auth, metrics=group_by_metrics["metrics"]
            )
        else:
            groupings_stream = Groupings(authenticator=auth)

        attributions_stream = Attributions(authenticator=auth)

        streams = [
            projects_stream,
            metrics_stream,
            groupings_stream,
            attributions_stream,
        ]

        project: str | None = config.get("project")
        metrics: list[str] | None = config.get("metrics")
        group_by: dict[str, Any] = config.get("group_by", {})
        default_groups: list[str] = group_by.get("default_groups", [])
        custom_groups: list[str] = group_by.get("custom_groups", [])
        groups: list[str] = list(set(default_groups) | set(custom_groups))
        top_count: int = config.get("top_count", 10000)
        split_by_days: bool = config.get("split_by_days", False)
        attribution_spec: dict[str, Any] | None = config.get("attribution_settings")
        attribution = (
            attribution_spec["attribution"]
            if attribution_spec["attribution_type"] == "attribution"
            else None
        )
        if project and metrics and group_by and top_count:
            streams.append(
                Reports(
                    authenticator=auth,
                    project=project,
                    metrics=metrics,
                    groups=groups,
                    top_count=top_count,
                    date_from=start_date,
                    date_to=end_date,
                    split_by_days=split_by_days,
                    attribution=attribution,
                )
            )
        return streams
