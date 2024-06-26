#
# Copyright (c) 2021 Airbyte, Inc., all rights reserved.
#

from operator import xor
from typing import Any, List, Mapping, Tuple

from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models import AdvancedAuth, AuthFlowType, ConnectorSpecification, OAuthConfigSpecification, SyncMode
from airbyte_cdk.models.airbyte_protocol import DestinationSyncMode
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator
from datetime import datetime, timedelta

from .spec import (
    CompleteOauthOutputSpecification,
    CompleteOauthServerInputSpecification,
    CompleteOauthServerOutputSpecification,
    SourceTiktokMarketingSpec,
)
from .streams import (
    DEFAULT_START_DATE,
    AdGroupAudienceReports,
    AdGroups,
    AdGroupsReports,
    Ads,
    AdsAudienceReports,
    AdsReports,
    Advertisers,
    AdvertisersAudienceReports,
    AdvertisersReports,
    Campaigns,
    CampaignsAudienceReportsByCountry,
    CampaignsReports,
    ReportGranularity,
    VideoCreatives,
)

DOCUMENTATION_URL = "https://docs.airbyte.io/integrations/sources/tiktok-marketing"


class TiktokTokenAuthenticator(TokenAuthenticator):
    """
    Docs: https://business-api.tiktok.com/marketing_api/docs?rid=sta6fe2yww&id=1701890922708994
    """

    def __init__(self, token: str, **kwargs):
        super().__init__(token, **kwargs)
        self.token = token

    def get_auth_header(self) -> Mapping[str, Any]:
        return {"Access-Token": self.token}


class SourceTiktokMarketing(AbstractSource):
    def spec(self, *args, **kwargs) -> ConnectorSpecification:
        """Returns the spec for this integration."""
        return ConnectorSpecification(
            documentationUrl=DOCUMENTATION_URL,
            changelogUrl=DOCUMENTATION_URL,
            supportsIncremental=True,
            supported_destination_sync_modes=[DestinationSyncMode.overwrite, DestinationSyncMode.append, DestinationSyncMode.append_dedup],
            connectionSpecification=SourceTiktokMarketingSpec.schema(),
            additionalProperties=True,
            advanced_auth=AdvancedAuth(
                auth_flow_type=AuthFlowType.oauth2_0,
                predicate_key=["credentials", "auth_type"],
                predicate_value="oauth2.0",
                oauth_config_specification=OAuthConfigSpecification(
                    complete_oauth_output_specification=CompleteOauthOutputSpecification.schema(),
                    complete_oauth_server_input_specification=CompleteOauthServerInputSpecification.schema(),
                    complete_oauth_server_output_specification=CompleteOauthServerOutputSpecification.schema(),
                ),
            ),
        )

    @staticmethod
    def _prepare_stream_args(config: Mapping[str, Any]) -> Mapping[str, Any]:
        """Converts an input configure to stream arguments"""
        credentials = config.get("credentials")
        if credentials:
            # used for new config format
            access_token = credentials["access_token"]
            secret = credentials.get("secret")
            app_id = int(credentials.get("app_id", 0))
            advertiser_id = int(credentials.get("advertiser_id", 0))
            splitted_advertisers_ids_filter = credentials.get("advertisers_ids_filter", "").split(",")
        else:
            access_token = config["access_token"]
            secret = config.get("environment", {}).get("secret")
            app_id = int(config.get("environment", {}).get("app_id", 0))
            advertiser_id = int(config.get("environment", {}).get("advertiser_id", 0))
            splitted_advertisers_ids_filter = config.get("environment", {}).get("advertisers_ids_filter", "").split(",")

        if splitted_advertisers_ids_filter == [""]:
            splitted_advertisers_ids_filter = []
        advertisers_ids_filter = list(map(int, splitted_advertisers_ids_filter))

        prepared = {
            "authenticator": TiktokTokenAuthenticator(access_token),
            "start_date": config.get("start_date"),
            "end_date": config.get("end_date"),
            "last_n_days": config.get("last_n_days"),
            "advertiser_id": advertiser_id,
            "app_id": app_id,
            "secret": secret,
            "advertisers_ids_filter": advertisers_ids_filter,
        }
        prepared = SourceTiktokMarketing.prepare_config_dates(prepared)
        return prepared

    @staticmethod
    def prepare_config_dates(config: Mapping[str, Any]) -> Mapping[str, Any]:
        config["backward_dates_campatibility_mode"] = False

        if (config.get("start_date") or config.get("end_date")) and config.get("last_n_days"):
            raise Exception(
                "You must specify either Date From and Date To or just "
                "Last Days (or only Date From for backward dates incremental behavior)"
            )

        if not config.get("start_date") and not config.get("last_n_days") and config.get("end_date"):
            raise Exception(
                "You must specify either Date From and Date To or just "
                "Last Days (or only Date From for backward dates incremental behavior)"
            )

        if config.get("start_date") and config.get("end_date"):
            pass
        elif config.get("start_date") and not config.get("end_date"):
            config["backward_dates_campatibility_mode"] = True
        elif not config.get("start_date") and not config.get("end_date") and not config.get("last_n_days"):
            config["backward_dates_campatibility_mode"] = True
            config["start_date"] = DEFAULT_START_DATE
        elif config.get("last_n_days"):
            config["start_date"] = str((datetime.now() - timedelta(days=config["last_n_days"])).date())
            config["end_date"] = str((datetime.now() - timedelta(days=1)).date())
        else:
            raise Exception("Invalid dates format or options")

        print(config)

        return config

    def check_connection(self, logger: AirbyteLogger, config: Mapping[str, Any]) -> Tuple[bool, any]:
        """
        Tests if the input configuration can be used to successfully connect to the integration
        """
        try:
            next(Advertisers(**self._prepare_stream_args(config)).read_records(SyncMode.full_refresh))
        except Exception as err:
            return False, err
        return True, None

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        args = self._prepare_stream_args(config)
        report_granularity = config.get("report_granularity") or ReportGranularity.default()
        report_args = dict(report_granularity=report_granularity, **args)
        advertisers_reports = AdvertisersReports(**report_args)
        streams = [
            Ads(**args),
            AdsReports(**report_args),
            Advertisers(**args),
            advertisers_reports if not advertisers_reports.is_sandbox else None,
            AdGroups(**args),
            AdGroupsReports(**report_args),
            VideoCreatives(**args),
            Campaigns(**args),
            CampaignsReports(**report_args),
            CampaignsAudienceReportsByCountry(**report_args),
            AdGroupAudienceReports(**report_args),
            AdsAudienceReports(**report_args),
            AdvertisersAudienceReports(**report_args),
        ]
        return [stream for stream in streams if stream]
