from ..field_manager import YandexMetrikaSourceField, YandexMetrikaFieldsManager

hits_fields: list[YandexMetrikaSourceField] = [
    YandexMetrikaSourceField("ym:pv:watchID", field_type="string", required=True),
    YandexMetrikaSourceField("ym:pv:dateTime", field_type="string", required=True),
    YandexMetrikaSourceField("ym:pv:counterID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:date", field_type="string"),
    YandexMetrikaSourceField("ym:pv:title", field_type="string"),
    YandexMetrikaSourceField("ym:pv:URL", field_type="string"),
    YandexMetrikaSourceField("ym:pv:referer", field_type="string"),
    YandexMetrikaSourceField("ym:pv:UTMCampaign", field_type="string"),
    YandexMetrikaSourceField("ym:pv:UTMContent", field_type="string"),
    YandexMetrikaSourceField("ym:pv:UTMMedium", field_type="string"),
    YandexMetrikaSourceField("ym:pv:UTMSource", field_type="string"),
    YandexMetrikaSourceField("ym:pv:UTMTerm", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browser", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserMajorVersion", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserMinorVersion", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserCountry", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserEngine", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserEngineVersion1", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserEngineVersion2", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserEngineVersion3", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserEngineVersion4", field_type="string"),
    YandexMetrikaSourceField("ym:pv:browserLanguage", field_type="string"),
    YandexMetrikaSourceField("ym:pv:clientTimeZone", field_type="string"),
    YandexMetrikaSourceField("ym:pv:cookieEnabled", field_type="string"),
    YandexMetrikaSourceField("ym:pv:deviceCategory", field_type="string"),
    YandexMetrikaSourceField("ym:pv:from", field_type="string"),
    YandexMetrikaSourceField("ym:pv:hasGCLID", field_type="boolean"),
    YandexMetrikaSourceField("ym:pv:GCLID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:ipAddress", field_type="string"),
    YandexMetrikaSourceField("ym:pv:javascriptEnabled", field_type="string"),
    YandexMetrikaSourceField("ym:pv:mobilePhone", field_type="string"),
    YandexMetrikaSourceField("ym:pv:mobilePhoneModel", field_type="string"),
    YandexMetrikaSourceField("ym:pv:openstatAd", field_type="string"),
    YandexMetrikaSourceField("ym:pv:openstatCampaign", field_type="string"),
    YandexMetrikaSourceField("ym:pv:openstatService", field_type="string"),
    YandexMetrikaSourceField("ym:pv:openstatSource", field_type="string"),
    YandexMetrikaSourceField("ym:pv:operatingSystem", field_type="string"),
    YandexMetrikaSourceField("ym:pv:operatingSystemRoot", field_type="string"),
    YandexMetrikaSourceField("ym:pv:physicalScreenHeight", field_type="string"),
    YandexMetrikaSourceField("ym:pv:physicalScreenWidth", field_type="string"),
    YandexMetrikaSourceField("ym:pv:regionCity", field_type="string"),
    YandexMetrikaSourceField("ym:pv:regionCountry", field_type="string"),
    YandexMetrikaSourceField("ym:pv:regionCityID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:regionCountryID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:screenColors", field_type="string"),
    YandexMetrikaSourceField("ym:pv:screenFormat", field_type="string"),
    YandexMetrikaSourceField("ym:pv:screenHeight", field_type="string"),
    YandexMetrikaSourceField("ym:pv:screenOrientation", field_type="string"),
    YandexMetrikaSourceField("ym:pv:screenWidth", field_type="string"),
    YandexMetrikaSourceField("ym:pv:windowClientHeight", field_type="string"),
    YandexMetrikaSourceField("ym:pv:windowClientWidth", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastTrafficSource", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastSearchEngine", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastSearchEngineRoot", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastAdvEngine", field_type="string"),
    YandexMetrikaSourceField("ym:pv:artificial", field_type="string"),
    YandexMetrikaSourceField("ym:pv:pageCharset", field_type="string"),
    YandexMetrikaSourceField("ym:pv:isPageView", field_type="string"),
    YandexMetrikaSourceField("ym:pv:link", field_type="string"),
    YandexMetrikaSourceField("ym:pv:download", field_type="string"),
    YandexMetrikaSourceField("ym:pv:notBounce", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastSocialNetwork", field_type="string"),
    YandexMetrikaSourceField("ym:pv:httpError", field_type="string"),
    YandexMetrikaSourceField("ym:pv:clientID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:networkType", field_type="string"),
    YandexMetrikaSourceField("ym:pv:lastSocialNetworkProfile", field_type="string"),
    YandexMetrikaSourceField("ym:pv:goalsID", field_type="string"),
    YandexMetrikaSourceField("ym:pv:shareService", field_type="string"),
    YandexMetrikaSourceField("ym:pv:shareURL", field_type="string"),
    YandexMetrikaSourceField("ym:pv:shareTitle", field_type="string"),
    YandexMetrikaSourceField("ym:pv:iFrame", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey1", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey2", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey3", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey4", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey5", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey6", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey7", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey8", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey9", field_type="string"),
    YandexMetrikaSourceField("ym:pv:parsedParamsKey10", field_type="string"),
    YandexMetrikaSourceField("ym:pv:counterUserIDHash", field_type="string"),
]

visits_fields: list[YandexMetrikaSourceField] = [
    YandexMetrikaSourceField(
        field_name="ym:s:visitID", field_type="integer", required=True
    ),
    YandexMetrikaSourceField(field_name="ym:s:counterID", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:watchIDs", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:date", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:dateTime", field_type="string", required=True
    ),
    YandexMetrikaSourceField(field_name="ym:s:dateTimeUTC", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:isNewUser", field_type="boolean"),
    YandexMetrikaSourceField(field_name="ym:s:startURL", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:endURL", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:pageViews", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:visitDuration", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:bounce", field_type="boolean"),
    YandexMetrikaSourceField(field_name="ym:s:ipAddress", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:regionCountry", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:regionCity", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:regionCountryID", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:regionCityID", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:clientID", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:counterUserIDHash", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:networkType", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:goalsID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:goalsSerialNumber", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:goalsDateTime", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:goalsPrice", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:goalsOrder", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:goalsCurrency", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>TrafficSource", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>AdvEngine", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>ReferalSource", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>SearchEngineRoot", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>SearchEngine", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>SocialNetwork", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>SocialNetworkProfile", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:referer", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectClickOrder", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectBannerGroup", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectClickBanner", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectClickOrderName", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>ClickBannerGroupName", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectClickBannerName", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectPhraseOrCond", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectPlatformType", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectPlatform", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>DirectConditionType", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>CurrencyID", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:from", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>UTMCampaign", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>UTMContent", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>UTMMedium", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>UTMSource", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>UTMTerm", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>openstatAd", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>openstatCampaign", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>openstatService", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>openstatSource", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>hasGCLID", field_type="boolean"
    ),
    YandexMetrikaSourceField(field_name="ym:s:<attribution>GCLID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:browserLanguage", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:browserCountry", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:clientTimeZone", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:deviceCategory", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:mobilePhone", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:mobilePhoneModel", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:operatingSystemRoot", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:operatingSystem", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:browser", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:browserMajorVersion", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:browserMinorVersion", field_type="integer"
    ),
    YandexMetrikaSourceField(field_name="ym:s:browserEngine", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:browserEngineVersion1", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:browserEngineVersion2", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:browserEngineVersion3", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:browserEngineVersion4", field_type="integer"
    ),
    YandexMetrikaSourceField(field_name="ym:s:cookieEnabled", field_type="boolean"),
    YandexMetrikaSourceField(field_name="ym:s:javascriptEnabled", field_type="boolean"),
    YandexMetrikaSourceField(field_name="ym:s:screenFormat", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:screenColors", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:screenOrientation", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:screenWidth", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:screenHeight", field_type="integer"),
    YandexMetrikaSourceField(
        field_name="ym:s:physicalScreenWidth", field_type="integer"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:physicalScreenHeight", field_type="integer"
    ),
    YandexMetrikaSourceField(field_name="ym:s:windowClientWidth", field_type="integer"),
    YandexMetrikaSourceField(
        field_name="ym:s:windowClientHeight", field_type="integer"
    ),
    YandexMetrikaSourceField(field_name="ym:s:purchaseID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:purchaseDateTime", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:purchaseAffiliation", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:purchaseRevenue", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:purchaseTax", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:purchaseShipping", field_type="integer"),
    YandexMetrikaSourceField(field_name="ym:s:purchaseCoupon", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:purchaseCurrency", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:purchaseProductQuantity", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductList", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductBrand", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory1", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory2", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory3", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory4", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCategory5", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductVariant", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductPosition", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductPrice", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCurrency", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductCoupon", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductQuantity", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductEventTime", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductType", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:eventsProductDiscount", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:eventsProductName", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsPurchaseID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsName", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsBrand", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory1", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory2", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory3", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory4", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCategory5", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsVariant", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsPosition", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsPrice", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCurrency", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsCoupon", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsQuantity", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsList", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsEventTime", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:productsDiscount", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:impressionsURL", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsDateTime", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductID", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductName", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductBrand", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory1", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory2", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory3", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory4", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCategory5", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductVariant", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductPrice", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCurrency", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductCoupon", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductList", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductQuantity", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductEventTime", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:impressionsProductDiscount", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:promotionID", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:promotionName", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:promotionCreative", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:promotionPosition", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:promotionCreativeSlot", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:promotionEventTime", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:promotionType", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:offlineCallTalkDuration", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:offlineCallHoldDuration", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:offlineCallMissed", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:offlineCallTag", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:offlineCallFirstTimeCaller", field_type="string"
    ),
    YandexMetrikaSourceField(field_name="ym:s:offlineCallURL", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey1", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey2", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey3", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey4", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey5", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey6", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey7", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey8", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey9", field_type="string"),
    YandexMetrikaSourceField(field_name="ym:s:parsedParamsKey10", field_type="string"),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>RecommendationSystem", field_type="string"
    ),
    YandexMetrikaSourceField(
        field_name="ym:s:<attribution>Messenger", field_type="string"
    ),
]

hits_fields_manager: YandexMetrikaFieldsManager = YandexMetrikaFieldsManager(
    fields=hits_fields
)
visits_fields_manager: YandexMetrikaFieldsManager = YandexMetrikaFieldsManager(
    fields=visits_fields
)
