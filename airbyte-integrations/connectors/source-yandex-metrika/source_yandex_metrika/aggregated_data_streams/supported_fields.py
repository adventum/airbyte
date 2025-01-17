from ..field_manager import YandexMetrikaFieldsManager, YandexMetrikaSourceField

fields: list[YandexMetrikaSourceField] = [
    YandexMetrikaSourceField("ym:s:visits", field_type="integer"),
    YandexMetrikaSourceField("ym:s:pageviews", field_type="integer"),
    YandexMetrikaSourceField("ym:s:users", field_type="integer"),
    YandexMetrikaSourceField("ym:s:bounceRate", field_type="number"),
    YandexMetrikaSourceField("ym:s:pageDepth", field_type="number"),
    YandexMetrikaSourceField("ym:s:avgVisitDurationSeconds", field_type="integer"),
    YandexMetrikaSourceField("ym:s:visitsPerDay", field_type="number"),
    YandexMetrikaSourceField("ym:s:visitsPerHour", field_type="number"),
    YandexMetrikaSourceField("ym:s:visitsPerMinute", field_type="number"),
    YandexMetrikaSourceField("ym:s:robotPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:goal<goal_id>conversionRate", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:goal<goal_id>userConversionRate", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:goal<goal_id>users", field_type="integer"),
    YandexMetrikaSourceField("ym:s:goal<goal_id>visits", field_type="integer"),
    YandexMetrikaSourceField("ym:s:goal<goal_id>reaches", field_type="integer"),
    YandexMetrikaSourceField("ym:s:goal<goal_id>reachesPerUser", field_type="number"),
    YandexMetrikaSourceField("ym:s:goal<goal_id>revenue", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:goal<goal_id><currency>revenue", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:goal<goal_id>converted<currency>Revenue", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:goal<goal_id>ecommercePurchases", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:goal<goal_id>ecommerce<currency>ConvertedRevenue", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:anyGoalConversionRate", field_type="number"),
    YandexMetrikaSourceField("ym:s:sumGoalReachesAny", field_type="integer"),
    YandexMetrikaSourceField("ym:s:paramsNumber", field_type="integer"),
    YandexMetrikaSourceField("ym:s:sumParams", field_type="integer"),
    YandexMetrikaSourceField("ym:s:avgParams", field_type="number"),
    YandexMetrikaSourceField("ym:s:percentNewVisitors", field_type="number"),
    YandexMetrikaSourceField("ym:s:newUsers", field_type="integer"),
    YandexMetrikaSourceField("ym:s:newUserVisitsPercentage", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:upToDaySinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToWeekSinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToMonthSinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToQuarterSinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToYearSinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:overYearSinceFirstVisitPercentage", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:oneVisitPerUserPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo3VisitsPerUserPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo7VisitsPerUserPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo31VisitsPerUserPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:over32VisitsPerUserPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:oneDayBetweenVisitsPercentage", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:upToWeekBetweenVisitsPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToMonthBetweenVisitsPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:overMonthBetweenVisitsPercentage", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:upToDayUserRecencyPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upToWeekUserRecencyPercentage", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:upToMonthUserRecencyPercentage", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:upToQuarterUserRecencyPercentage", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:upToYearUserRecencyPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:overYearUserRecencyPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:avgDaysBetweenVisits", field_type="number"),
    YandexMetrikaSourceField("ym:s:avgDaysSinceFirstVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:userRecencyDays", field_type="number"),
    YandexMetrikaSourceField("ym:s:manPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:womanPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:under18AgePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo24AgePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo34AgePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:upTo44AgePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:over44AgePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:cookieEnabledPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:jsEnabledPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:mobilePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:productImpressions", field_type="integer"),
    YandexMetrikaSourceField("ym:s:productImpressionsUniq", field_type="integer"),
    YandexMetrikaSourceField("ym:s:productBasketsQuantity", field_type="integer"),
    YandexMetrikaSourceField("ym:s:productBasketsPrice", field_type="number"),
    YandexMetrikaSourceField("ym:s:productBasketsUniq", field_type="integer"),
    YandexMetrikaSourceField("ym:s:productPurchasedQuantity", field_type="integer"),
    YandexMetrikaSourceField("ym:s:productPurchasedPrice", field_type="number"),
    YandexMetrikaSourceField("ym:s:productPurchasedUniq", field_type="integer"),
    YandexMetrikaSourceField("ym:s:ecommercePurchases", field_type="integer"),
    YandexMetrikaSourceField("ym:s:ecommerceRevenue", field_type="number"),
    YandexMetrikaSourceField("ym:s:ecommerceRevenuePerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:ecommerceRevenuePerPurchase", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:ecommerce<currency>ConvertedRevenue", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:offlineCalls", field_type="integer"),
    YandexMetrikaSourceField("ym:s:offlineCallsMissed", field_type="integer"),
    YandexMetrikaSourceField("ym:s:offlineCallsMissedPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:s:offlineCallsFirstTimeCaller", field_type="integer"),
    YandexMetrikaSourceField(
        "ym:s:offlineCallsFirstTimeCallerPercentage", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:offlineCallsUniq", field_type="integer"),
    YandexMetrikaSourceField("ym:s:offlineCallTalkDurationAvg", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:offlineCallHoldDurationTillAnswerAvg", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:offlineCallHoldDurationTillMissAvg", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:offlineCallDurationAvg", field_type="number"),
    YandexMetrikaSourceField("ym:s:offlineCallRevenueAvg", field_type="number"),
    YandexMetrikaSourceField("ym:s:offlineCallRevenue", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRequests", field_type="integer"),
    YandexMetrikaSourceField("ym:s:yanRenders", field_type="integer"),
    YandexMetrikaSourceField("ym:s:yanShows", field_type="integer"),
    YandexMetrikaSourceField("ym:s:yanPartnerPrice", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanCPMV", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanECPM", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRPM", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanVisibility", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanARPU", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRendersPerUser", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRevenuePerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRevenuePerHit", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRendersPerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:yanRendersPerHit", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxRequests", field_type="integer"),
    YandexMetrikaSourceField("ym:s:adfoxRenders", field_type="integer"),
    YandexMetrikaSourceField("ym:s:adfoxRendersDefault", field_type="integer"),
    YandexMetrikaSourceField("ym:s:adfoxShows", field_type="integer"),
    YandexMetrikaSourceField("ym:s:adfoxClicks", field_type="integer"),
    YandexMetrikaSourceField("ym:s:adfoxVisibility", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxRendersPerUser", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxRendersPerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxRendersPerHit", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPrice", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxCPMV", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxECPM", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxRPM", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxARPU", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPricePerUser", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPricePerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPricePerHit", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPriceStrict", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPriceYan", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPriceGoogle", field_type="number"),
    YandexMetrikaSourceField("ym:s:adfoxPriceHeaderBidding", field_type="number"),
    YandexMetrikaSourceField(
        "ym:s:sumPublisherArticleInvolvedTimeSeconds", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:s:avgPublisherArticleInvolvedTimeSeconds", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:publisherviews", field_type="integer"),
    YandexMetrikaSourceField("ym:s:publisherviewsPerDay", field_type="number"),
    YandexMetrikaSourceField("ym:s:publisherviewsPerHour", field_type="number"),
    YandexMetrikaSourceField("ym:s:publisherviewsPerMinute", field_type="number"),
    YandexMetrikaSourceField("ym:s:publisherusers", field_type="integer"),
    YandexMetrikaSourceField(
        "ym:s:publisherArticleUsersRecircled", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:publisherArticleRecirculation", field_type="number"),
    YandexMetrikaSourceField("ym:s:publisherViewsFullScroll", field_type="integer"),
    YandexMetrikaSourceField(
        "ym:s:publisherArticleViewsFullScrollShare", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:publisherViewsFullRead", field_type="integer"),
    YandexMetrikaSourceField("ym:s:publisherArticleFullReadShare", field_type="number"),
    YandexMetrikaSourceField("ym:s:publisherMobileOrTabletViews", field_type="integer"),
    YandexMetrikaSourceField(
        "ym:s:publisherMobileOrTabletViewsShare", field_type="number"
    ),
    YandexMetrikaSourceField("ym:s:vacuumevents", field_type="integer"),
    YandexMetrikaSourceField("ym:s:vacuumusers", field_type="integer"),
    YandexMetrikaSourceField("ym:s:vacuumeventsPerUser", field_type="number"),
    YandexMetrikaSourceField("ym:s:affinityIndexInterests", field_type="number"),
    YandexMetrikaSourceField("ym:s:affinityIndexInterests2", field_type="number"),
    YandexMetrikaSourceField("ym:s:GCLIDPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:pv:pageviews", field_type="integer"),
    YandexMetrikaSourceField("ym:pv:users", field_type="integer"),
    YandexMetrikaSourceField("ym:pv:pageviewsPerDay", field_type="number"),
    YandexMetrikaSourceField("ym:pv:pageviewsPerHour", field_type="number"),
    YandexMetrikaSourceField("ym:pv:pageviewsPerMinute", field_type="number"),
    YandexMetrikaSourceField("ym:pv:cookieEnabledPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:pv:jsEnabledPercentage", field_type="number"),
    YandexMetrikaSourceField("ym:pv:mobilePercentage", field_type="number"),
    YandexMetrikaSourceField("ym:ad:visits", field_type="integer"),
    YandexMetrikaSourceField("ym:ad:clicks", field_type="integer"),
    YandexMetrikaSourceField("ym:ad:<currency>AdCost", field_type="number"),
    YandexMetrikaSourceField("ym:ad:<currency>AdCostPerVisit", field_type="number"),
    YandexMetrikaSourceField("ym:ad:goal<goal_id><currency>CPA", field_type="number"),
    YandexMetrikaSourceField(
        "ym:ad:goal<goal_id><currency>AdCostPerVisit", field_type="number"
    ),
    YandexMetrikaSourceField("ym:up:params", field_type="integer"),
    YandexMetrikaSourceField("ym:up:users", field_type="integer"),
    YandexMetrikaSourceField("ym:ev:expenses<currency>", field_type="number"),
    YandexMetrikaSourceField("ym:ev:expenseClicks", field_type="integer"),
    YandexMetrikaSourceField("ym:ev:expense<currency>CPC", field_type="number"),
    YandexMetrikaSourceField(
        "ym:ev:expense<currency>EcommerceROI", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:goal<goal_id>expense<currency>ROI", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:expense<currency>EcommerceCPA", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:goal<goal_id>expense<currency>ReachCPA", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:goal<goal_id>expense<currency>VisitCPA", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:goal<goal_id>expense<currency>UserCPA", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:expense<currency>EcommerceCRR", field_type="number"
    ),
    YandexMetrikaSourceField(
        "ym:ev:goal<goal_id>expense<currency>CRR", field_type="number"
    ),
]

aggregated_data_streams_fields_manager: YandexMetrikaFieldsManager = (
    YandexMetrikaFieldsManager(fields=fields)
)
