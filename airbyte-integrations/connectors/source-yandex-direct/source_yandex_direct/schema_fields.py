CUSTOM_SCHEMA_FIELDS = {
    "AdFormat": "string",
    "AdGroupId": "string",
    "AdGroupName": "string",
    "AdId": "string",
    "AdNetworkType": "string",
    "Age": "string",
    "AudienceTargetId": "filter",
    "AvgClickPosition": "string",
    "AvgCpc": "string",
    "AvgCpm": None,
    "AvgEffectiveBid": "string",
    "AvgImpressionFrequency": None,
    "AvgImpressionPosition": "string",
    "AvgPageviews": "string",
    "AvgTrafficVolume": "string",
    "BounceRate": "string",
    "Bounces": "string",
    "CampaignId": "string",
    "CampaignName": "string",
    "CampaignType": "string",
    "CarrierType": "string",
    "Clicks": "string",
    "ClickType": "string",
    "ConversionRate": "string",
    "Conversions": "string",
    "Cost": "string",
    "CostPerConversion": "string",
    "Criteria": "string",
    "CriteriaId": "string",
    "CriteriaType": "string",
    "Criterion": "string",
    "CriterionId": "string",
    "CriterionType": "string",
    "Ctr": "string",
    "Date": "string",
    "Device": "string",
    "DynamicTextAdTargetId": "filter",
    "ExternalNetworkName": "string",
    "Gender": "string",
    "GoalsRoi": "string",
    "ImpressionReach": None,
    "Impressions": "string",
    "ImpressionShare": None,
    "IncomeGrade": "string",
    "Keyword": "filter",
    "LocationOfPresenceId": "string",
    "LocationOfPresenceName": "string",
    "MatchedKeyword": None,
    "MatchType": "string",
    "MobilePlatform": "string",
    "Month": "string",
    "Placement": "string",
    "Profit": "string",
    "Quarter": "string",
    "Query": None,
    "Revenue": "string",
    "RlAdjustmentId": "string",
    "Sessions": "string",
    "Slot": "string",
    "SmartAdTargetId": "filter",
    "TargetingCategory": "string",
    "TargetingLocationId": "string",
    "TargetingLocationName": "string",
    "Week": "string",
    "WeightedCtr": "string",
    "WeightedImpressions": "string",
    "Year": "string",
}

ADS_DEFAULT_FIELDS = {
    "FieldNames": [
        "AdCategories",
        "AgeLabel",
        "AdGroupId",
        "CampaignId",
        "Id",
        "State",
        "Status",
        "StatusClarification",
        "Type",
        "Subtype",
    ],
    "TextAdFieldNames": [
        "AdImageHash",
        "DisplayDomain",
        "Href",
        "SitelinkSetId",
        "Text",
        "Title",
        "Title2",
        "Mobile",
        "VCardId",
        "DisplayUrlPath",
        "AdImageModeration",
        "SitelinksModeration",
        "VCardModeration",
        "AdExtensions",
        "DisplayUrlPathModeration",
        "VideoExtension",
        "TurboPageId",
        "TurboPageModeration",
        "BusinessId",
    ],
    "TextAdPriceExtensionFieldNames": ["Price", "OldPrice", "PriceCurrency", "PriceQualifier"],
    "MobileAppAdFieldNames": [
        "AdImageHash",
        "AdImageModeration",
        "Title",
        "Text",
        "Features",
        "Action",
        "TrackingUrl",
        "VideoExtension",
    ],
    "DynamicTextAdFieldNames": [
        "AdImageHash",
        "SitelinkSetId",
        "Text",
        "VCardId",
        "AdImageModeration",
        "SitelinksModeration",
        "VCardModeration",
        "AdExtensions",
    ],
    "TextImageAdFieldNames": ["AdImageHash", "Href", "TurboPageId", "TurboPageModeration"],
    "MobileAppImageAdFieldNames": ["AdImageHash", "TrackingUrl"],
    "TextAdBuilderAdFieldNames": ["Creative", "Href", "TurboPageId", "TurboPageModeration"],
    "MobileAppAdBuilderAdFieldNames": ["Creative", "TrackingUrl"],
    "MobileAppCpcVideoAdBuilderAdFieldNames": ["Creative", "TrackingUrl"],
    "CpcVideoAdBuilderAdFieldNames": ["Creative", "Href", "TurboPageId", "TurboPageModeration"],
    "CpmBannerAdBuilderAdFieldNames": [
        "Creative",
        "Href",
        "TrackingPixels",
        "TurboPageId",
        "TurboPageModeration",
    ],
    "CpmVideoAdBuilderAdFieldNames": [
        "Creative",
        "Href",
        "TrackingPixels",
        "TurboPageId",
        "TurboPageModeration",
    ],
    "SmartAdBuilderAdFieldNames": ["Creative"],
}

AD_IMAGES_DEFAULT_FIELDS = {
    "FieldNames": [
        "AdImageHash",
        "OriginalUrl",
        "PreviewUrl",
        "Name",
        "Type",
        "Subtype",
        "Associated",
    ],
}

CAMPAIGNS_DEFAULT_FIELDS = {
    "FieldNames": [
        "Id",
        "Name",
        "StartDate",
        "Type",
        "Status",
        "State",
        "StatusPayment",
        "StatusClarification",
        "SourceId",
        "Currency",
        "DailyBudget",
        "EndDate",
        "ClientInfo",
    ],
    "TextCampaignFieldNames": [
        "CounterIds",
        "RelevantKeywords",
        "Settings",
        "BiddingStrategy",
        "PriorityGoals",
        "AttributionModel",
        "PackageBiddingStrategy",
        "CanBeUsedAsPackageBiddingStrategySource",
        "NegativeKeywordSharedSetIds",
    ]
}


def build_goal_fields(
    field_name: str, goal_ids: list[str], attribution_models: list[str]
) -> list[str]:
    # ConversionRate_<id_цели>_<модель>
    # Conversions_<id_цели>_<модель>
    # CostPerConversion_<id_цели>_<модель>
    # GoalsRoi_<id_цели>_<модель>
    # Revenue_<id_цели>_<модель>
    if not attribution_models:
        attribution_models = ["LSC"]

    goal_fields = []
    for goal_id in goal_ids:
        for attribution_model in attribution_models:
            goal_fields.append(f"{field_name}_{goal_id}_{attribution_model}")
    return goal_fields
