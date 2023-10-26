from typing import List


class YandexMetrikaSourceFields:
    def __init__(self, fields: dict):
        self._fields = fields

    def get_all_fields_names_list(self) -> List[str]:
        return [f["name"] for f in self._fields["all"]]

    def get_required_fields_names_list(self) -> List[str]:
        return [f["name"] for f in self._fields["required"]]

    def get_all_fields(self) -> list[dict]:
        return self._fields["all"]

    def get_required_fields(self) -> list[dict]:
        return self._fields["required"]


HITS_AVAILABLE_FIELDS = YandexMetrikaSourceFields(
    {
        "required": [
            {"name": "ym:pv:watchID", "type": "string"},
            {"name": "ym:pv:dateTime", "type": "string"},
        ],
        "all": [
            {"name": "ym:pv:watchID", "type": "string"},
            {"name": "ym:pv:counterID", "type": "string"},
            {"name": "ym:pv:date", "type": "string"},
            {"name": "ym:pv:dateTime", "type": "string"},
            {"name": "ym:pv:title", "type": "string"},
            {"name": "ym:pv:URL", "type": "string"},
            {"name": "ym:pv:referer", "type": "string"},
            {"name": "ym:pv:UTMCampaign", "type": "string"},
            {"name": "ym:pv:UTMContent", "type": "string"},
            {"name": "ym:pv:UTMMedium", "type": "string"},
            {"name": "ym:pv:UTMSource", "type": "string"},
            {"name": "ym:pv:UTMTerm", "type": "string"},
            {"name": "ym:pv:browser", "type": "string"},
            {"name": "ym:pv:browserMajorVersion", "type": "string"},
            {"name": "ym:pv:browserMinorVersion", "type": "string"},
            {"name": "ym:pv:browserCountry", "type": "string"},
            {"name": "ym:pv:browserEngine", "type": "string"},
            {"name": "ym:pv:browserEngineVersion1", "type": "string"},
            {"name": "ym:pv:browserEngineVersion2", "type": "string"},
            {"name": "ym:pv:browserEngineVersion3", "type": "string"},
            {"name": "ym:pv:browserEngineVersion4", "type": "string"},
            {"name": "ym:pv:browserLanguage", "type": "string"},
            {"name": "ym:pv:clientTimeZone", "type": "string"},
            {"name": "ym:pv:cookieEnabled", "type": "string"},
            {"name": "ym:pv:deviceCategory", "type": "string"},
            {"name": "ym:pv:from", "type": "string"},
            {"name": "ym:pv:hasGCLID", "type": "string"},
            {"name": "ym:pv:GCLID", "type": "string"},
            {"name": "ym:pv:ipAddress", "type": "string"},
            {"name": "ym:pv:javascriptEnabled", "type": "string"},
            {"name": "ym:pv:mobilePhone", "type": "string"},
            {"name": "ym:pv:mobilePhoneModel", "type": "string"},
            {"name": "ym:pv:openstatAd", "type": "string"},
            {"name": "ym:pv:openstatCampaign", "type": "string"},
            {"name": "ym:pv:openstatService", "type": "string"},
            {"name": "ym:pv:openstatSource", "type": "string"},
            {"name": "ym:pv:operatingSystem", "type": "string"},
            {"name": "ym:pv:operatingSystemRoot", "type": "string"},
            {"name": "ym:pv:physicalScreenHeight", "type": "string"},
            {"name": "ym:pv:physicalScreenWidth", "type": "string"},
            {"name": "ym:pv:regionCity", "type": "string"},
            {"name": "ym:pv:regionCountry", "type": "string"},
            {"name": "ym:pv:regionCityID", "type": "string"},
            {"name": "ym:pv:regionCountryID", "type": "string"},
            {"name": "ym:pv:screenColors", "type": "string"},
            {"name": "ym:pv:screenFormat", "type": "string"},
            {"name": "ym:pv:screenHeight", "type": "string"},
            {"name": "ym:pv:screenOrientation", "type": "string"},
            {"name": "ym:pv:screenWidth", "type": "string"},
            {"name": "ym:pv:windowClientHeight", "type": "string"},
            {"name": "ym:pv:windowClientWidth", "type": "string"},
            {"name": "ym:pv:lastTrafficSource", "type": "string"},
            {"name": "ym:pv:lastSearchEngine", "type": "string"},
            {"name": "ym:pv:lastSearchEngineRoot", "type": "string"},
            {"name": "ym:pv:lastAdvEngine", "type": "string"},
            {"name": "ym:pv:artificial", "type": "string"},
            {"name": "ym:pv:pageCharset", "type": "string"},
            {"name": "ym:pv:isPageView", "type": "string"},
            {"name": "ym:pv:link", "type": "string"},
            {"name": "ym:pv:download", "type": "string"},
            {"name": "ym:pv:notBounce", "type": "string"},
            {"name": "ym:pv:lastSocialNetwork", "type": "string"},
            {"name": "ym:pv:httpError", "type": "string"},
            {"name": "ym:pv:clientID", "type": "string"},
            {"name": "ym:pv:networkType", "type": "string"},
            {"name": "ym:pv:lastSocialNetworkProfile", "type": "string"},
            {"name": "ym:pv:goalsID", "type": "string"},
            {"name": "ym:pv:shareService", "type": "string"},
            {"name": "ym:pv:shareURL", "type": "string"},
            {"name": "ym:pv:shareTitle", "type": "string"},
            {"name": "ym:pv:iFrame", "type": "string"},
            {"name": "ym:pv:parsedParamsKey1", "type": "string"},
            {"name": "ym:pv:parsedParamsKey2", "type": "string"},
            {"name": "ym:pv:parsedParamsKey3", "type": "string"},
            {"name": "ym:pv:parsedParamsKey4", "type": "string"},
            {"name": "ym:pv:parsedParamsKey5", "type": "string"},
            {"name": "ym:pv:parsedParamsKey6", "type": "string"},
            {"name": "ym:pv:parsedParamsKey7", "type": "string"},
            {"name": "ym:pv:parsedParamsKey8", "type": "string"},
            {"name": "ym:pv:parsedParamsKey9", "type": "string"},
            {"name": "ym:pv:parsedParamsKey10", "type": "string"},
            {"name": "ym:pv:counterUserIDHash", "type": "string"},
        ],
    }
)

VISITS_AVAILABLE_FIELDS = YandexMetrikaSourceFields(
    {
        "required": [{"name": "ym:s:visitID", "type": "string"}, {"name": "ym:s:dateTime", "type": "string"}],
        "all": [
            {"name": "ym:s:visitID", "type": "string"},
            {"name": "ym:s:counterID", "type": "string"},
            {"name": "ym:s:watchIDs", "type": "string"},
            {"name": "ym:s:date", "type": "string"},
            {"name": "ym:s:dateTime", "type": "string"},
            {"name": "ym:s:dateTimeUTC", "type": "string"},
            {"name": "ym:s:counterUserIDHash", "type": "string"},
            {"name": "ym:s:isNewUser", "type": "boolean"},
            {"name": "ym:s:startURL", "type": "string"},
            {"name": "ym:s:endURL", "type": "string"},
            {"name": "ym:s:pageViews", "type": "string"},
            {"name": "ym:s:visitDuration", "type": "string"},
            {"name": "ym:s:bounce", "type": "string"},
            {"name": "ym:s:ipAddress", "type": "string"},
            {"name": "ym:s:regionCountry", "type": "string"},
            {"name": "ym:s:regionCity", "type": "string"},
            {"name": "ym:s:regionCountryID", "type": "string"},
            {"name": "ym:s:regionCityID", "type": "string"},
            {"name": "ym:s:clientID", "type": "string"},
            {"name": "ym:s:networkType", "type": "string"},
            {"name": "ym:s:goalsID", "type": "string"},
            {"name": "ym:s:goalsSerialNumber", "type": "string"},
            {"name": "ym:s:goalsDateTime", "type": "string"},
            {"name": "ym:s:goalsPrice", "type": "string"},
            {"name": "ym:s:goalsOrder", "type": "string"},
            {"name": "ym:s:goalsCurrency", "type": "string"},
            {"name": "ym:s:lastTrafficSource", "type": "string"},
            {"name": "ym:s:lastAdvEngine", "type": "string"},
            {"name": "ym:s:lastReferalSource", "type": "string"},
            {"name": "ym:s:lastSearchEngineRoot", "type": "string"},
            {"name": "ym:s:lastSearchEngine", "type": "string"},
            {"name": "ym:s:lastSocialNetwork", "type": "string"},
            {"name": "ym:s:lastSocialNetworkProfile", "type": "string"},
            {"name": "ym:s:referer", "type": "string"},
            {"name": "ym:s:lastDirectClickOrder", "type": "string"},
            {"name": "ym:s:lastDirectBannerGroup", "type": "string"},
            {"name": "ym:s:lastDirectClickBanner", "type": "string"},
            {"name": "ym:s:lastDirectClickOrderName", "type": "string"},
            {"name": "ym:s:lastClickBannerGroupName", "type": "string"},
            {"name": "ym:s:lastDirectClickBannerName", "type": "string"},
            {"name": "ym:s:lastDirectPhraseOrCond", "type": "string"},
            {"name": "ym:s:lastDirectPlatformType", "type": "string"},
            {"name": "ym:s:lastDirectPlatform", "type": "string"},
            {"name": "ym:s:lastDirectConditionType", "type": "string"},
            {"name": "ym:s:lastCurrencyID", "type": "string"},
            {"name": "ym:s:from", "type": "string"},
            {"name": "ym:s:UTMCampaign", "type": "string"},
            {"name": "ym:s:UTMContent", "type": "string"},
            {"name": "ym:s:UTMMedium", "type": "string"},
            {"name": "ym:s:UTMSource", "type": "string"},
            {"name": "ym:s:UTMTerm", "type": "string"},
            {"name": "ym:s:openstatAd", "type": "string"},
            {"name": "ym:s:openstatCampaign", "type": "string"},
            {"name": "ym:s:openstatService", "type": "string"},
            {"name": "ym:s:openstatSource", "type": "string"},
            {"name": "ym:s:hasGCLID", "type": "string"},
            {"name": "ym:s:lastGCLID", "type": "string"},
            {"name": "ym:s:firstGCLID", "type": "string"},
            {"name": "ym:s:lastSignificantGCLID", "type": "string"},
            {"name": "ym:s:browserLanguage", "type": "string"},
            {"name": "ym:s:browserCountry", "type": "string"},
            {"name": "ym:s:clientTimeZone", "type": "string"},
            {"name": "ym:s:deviceCategory", "type": "string"},
            {"name": "ym:s:mobilePhone", "type": "string"},
            {"name": "ym:s:mobilePhoneModel", "type": "string"},
            {"name": "ym:s:operatingSystemRoot", "type": "string"},
            {"name": "ym:s:operatingSystem", "type": "string"},
            {"name": "ym:s:browser", "type": "string"},
            {"name": "ym:s:browserMajorVersion", "type": "string"},
            {"name": "ym:s:browserMinorVersion", "type": "string"},
            {"name": "ym:s:browserEngine", "type": "string"},
            {"name": "ym:s:browserEngineVersion1", "type": "string"},
            {"name": "ym:s:browserEngineVersion2", "type": "string"},
            {"name": "ym:s:browserEngineVersion3", "type": "string"},
            {"name": "ym:s:browserEngineVersion4", "type": "string"},
            {"name": "ym:s:cookieEnabled", "type": "string"},
            {"name": "ym:s:javascriptEnabled", "type": "string"},
            {"name": "ym:s:screenFormat", "type": "string"},
            {"name": "ym:s:screenColors", "type": "string"},
            {"name": "ym:s:screenOrientation", "type": "string"},
            {"name": "ym:s:screenWidth", "type": "string"},
            {"name": "ym:s:screenHeight", "type": "string"},
            {"name": "ym:s:physicalScreenWidth", "type": "string"},
            {"name": "ym:s:physicalScreenHeight", "type": "string"},
            {"name": "ym:s:windowClientWidth", "type": "string"},
            {"name": "ym:s:windowClientHeight", "type": "string"},
            {"name": "ym:s:purchaseID", "type": "string"},
            {"name": "ym:s:purchaseDateTime", "type": "string"},
            {"name": "ym:s:purchaseAffiliation", "type": "string"},
            {"name": "ym:s:purchaseRevenue", "type": "string"},
            {"name": "ym:s:purchaseTax", "type": "string"},
            {"name": "ym:s:purchaseShipping", "type": "string"},
            {"name": "ym:s:purchaseCoupon", "type": "string"},
            {"name": "ym:s:purchaseCurrency", "type": "string"},
            {"name": "ym:s:purchaseProductQuantity", "type": "string"},
            {"name": "ym:s:productsPurchaseID", "type": "string"},
            {"name": "ym:s:productsID", "type": "string"},
            {"name": "ym:s:productsName", "type": "string"},
            {"name": "ym:s:productsBrand", "type": "string"},
            {"name": "ym:s:productsCategory", "type": "string"},
            {"name": "ym:s:productsCategory1", "type": "string"},
            {"name": "ym:s:productsCategory2", "type": "string"},
            {"name": "ym:s:productsCategory3", "type": "string"},
            {"name": "ym:s:productsCategory4", "type": "string"},
            {"name": "ym:s:productsCategory5", "type": "string"},
            {"name": "ym:s:productsVariant", "type": "string"},
            {"name": "ym:s:productsPosition", "type": "string"},
            {"name": "ym:s:productsPrice", "type": "string"},
            {"name": "ym:s:productsCurrency", "type": "string"},
            {"name": "ym:s:productsCoupon", "type": "string"},
            {"name": "ym:s:productsQuantity", "type": "string"},
            {"name": "ym:s:impressionsURL", "type": "string"},
            {"name": "ym:s:impressionsDateTime", "type": "string"},
            {"name": "ym:s:impressionsProductID", "type": "string"},
            {"name": "ym:s:impressionsProductName", "type": "string"},
            {"name": "ym:s:impressionsProductBrand", "type": "string"},
            {"name": "ym:s:impressionsProductCategory", "type": "string"},
            {"name": "ym:s:impressionsProductCategory1", "type": "string"},
            {"name": "ym:s:impressionsProductCategory2", "type": "string"},
            {"name": "ym:s:impressionsProductCategory3", "type": "string"},
            {"name": "ym:s:impressionsProductCategory4", "type": "string"},
            {"name": "ym:s:impressionsProductCategory5", "type": "string"},
            {"name": "ym:s:impressionsProductVariant", "type": "string"},
            {"name": "ym:s:impressionsProductPrice", "type": "string"},
            {"name": "ym:s:impressionsProductCurrency", "type": "string"},
            {"name": "ym:s:impressionsProductCoupon", "type": "string"},
            {"name": "ym:s:offlineCallTalkDuration", "type": "string"},
            {"name": "ym:s:offlineCallHoldDuration", "type": "string"},
            {"name": "ym:s:offlineCallMissed", "type": "string"},
            {"name": "ym:s:offlineCallTag", "type": "string"},
            {"name": "ym:s:offlineCallFirstTimeCaller", "type": "string"},
            {"name": "ym:s:offlineCallURL", "type": "string"},
            {"name": "ym:s:parsedParamsKey1", "type": "string"},
            {"name": "ym:s:parsedParamsKey2", "type": "string"},
            {"name": "ym:s:parsedParamsKey3", "type": "string"},
            {"name": "ym:s:parsedParamsKey4", "type": "string"},
            {"name": "ym:s:parsedParamsKey5", "type": "string"},
            {"name": "ym:s:parsedParamsKey6", "type": "string"},
            {"name": "ym:s:parsedParamsKey7", "type": "string"},
            {"name": "ym:s:parsedParamsKey8", "type": "string"},
            {"name": "ym:s:parsedParamsKey9", "type": "string"},
            {"name": "ym:s:parsedParamsKey10", "type": "string"},
        ],
    }
)
