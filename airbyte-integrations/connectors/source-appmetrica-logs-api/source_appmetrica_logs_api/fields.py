AVAILABLE_FIELDS = {
    "clicks": {
        "fields": {
            "application_id": "integer",
            "click_datetime": "string",
            "click_id": "string",
            "click_ipv6": "string",
            "click_timestamp": "integer",
            "click_url_parameters": "string",
            "click_user_agent": "string",
            "publisher_id": "integer",
            "publisher_name": "string",
            "tracker_name": "string",
            "tracking_id": "integer",
            "touch_type": "string",
            "city": "string",
            "country_iso_code": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "oaid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "os_name": "string",
            "os_version": "string",
            "windows_aid": "string",
        },
    },
    "installations": {
        "fields": {
            "application_id": "integer",
            "installation_id": "string",
            "attributed_touch_type": "string",
            "click_datetime": "string",
            "click_id": "string",
            "click_ipv6": "string",
            "click_timestamp": "integer",
            "click_url_parameters": "string",
            "click_user_agent": "string",
            "profile_id": "string",
            "publisher_id": "integer",
            "publisher_name": "string",
            "tracker_name": "string",
            "tracking_id": "integer",
            "install_datetime": "string",
            "install_ipv6": "string",
            "install_receive_datetime": "string",
            "install_receive_timestamp": "integer",
            "install_timestamp": "integer",
            "is_reattribution": "string",
            "is_reinstallation": "string",
            "match_type": "string",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "oaid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "os_name": "string",
            "os_version": "string",
            "windows_aid": "string",
            "app_package_name": "string",
            "app_version_name": "string",
        },
    },
    "postbacks": {
        "fields": {
            "application_id": "integer",
            "attributed_touch_type": "string",
            "click_datetime": "string",
            "click_id": "string",
            "click_ipv6": "string",
            "click_timestamp": "integer",
            "click_url_parameters": "string",
            "click_user_agent": "string",
            "profile_id": "string",
            "publisher_id": "integer",
            "publisher_name": "string",
            "tracker_name": "string",
            "tracking_id": "integer",
            "install_datetime": "string",
            "install_ipv6": "string",
            "install_timestamp": "integer",
            "match_type": "string",
            "identifier": "string",
            "appmetrica_device_id": "string",
            "city": "string",
            "country_iso_code": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "oaid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "os_name": "string",
            "os_version": "string",
            "windows_aid": "string",
            "app_package_name": "string",
            "app_version_name": "string",
            "conversion_datetime": "string",
            "conversion_timestamp": "integer",
            "event_name": "string",
            "attempt_datetime": "string",
            "attempt_timestamp": "integer",
            "cost_model": "string",
            "notifying_status": "string",
            "postback_url": "string",
            "postback_url_parameters": "string",
            "response_body": "string",
            "response_code": "integer",
        },
    },
    "events": {
        "fields": {
            "event_datetime": "string",
            "event_json": "string",
            "event_name": "string",
            "event_receive_datetime": "string",
            "event_receive_timestamp": "integer",
            "event_timestamp": "integer",
            "session_id": "integer",
            "installation_id": "string",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "original_device_model": "string",
            "os_name": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_build_number": "integer",
            "app_package_name": "string",
            "app_version_name": "string",
            "application_id": "integer",
        }
    },
    "profiles": {
        "fields": {
            "profile_id": "string",
            "appmetrica_gender": "string",
            "appmetrica_birth_date": "string",
            "appmetrica_notifications_enabled": "string",
            "appmetrica_name": "string",
            "appmetrica_crashes": "integer",
            "appmetrica_errors": "integer",
            "appmetrica_first_session_date": "string",
            "appmetrica_last_start_date": "string",
            "appmetrica_push_opens": "integer",
            "appmetrica_push_send_count": "integer",
            "appmetrica_sdk_version": "integer",
            "appmetrica_sessions": "integer",
            "android_id": "string",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "os_name": "string",
            "os_version": "string",
            "windows_aid": "string",
            "app_build_number": "integer",
            "app_framework": "integer",
            "app_package_name": "string",
            "app_version_name": "string",
        }
    },
    "revenue_events": {
        "fields": {
            "revenue_quantity": "integer",
            "revenue_price": "string",
            "revenue_currency": "string",
            "revenue_product_id": "string",
            "revenue_order_id": "string",
            "revenue_order_id_source": "string",
            "is_revenue_verified": "string",
            "is_revenue_autocollected": "string",
            "event_name": "string",
            "event_receive_datetime": "string",
            "event_receive_timestamp": "integer",
            "event_timestamp": "integer",
            "session_id": "integer",
            "installation_id": "string",
            "android_id": "string",
            "appmetrica_device_id": "string",
            "appmetrica_sdk_version": "integer",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "event_datetime": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "original_device_model": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_build_number": "integer",
            "app_package_name": "string",
            "app_version_name": "string",
        }
    },
    "deeplinks": {
        "fields": {
            "deeplink_url_host": "string",
            "deeplink_url_parameters": "string",
            "deeplink_url_path": "string",
            "deeplink_url_scheme": "string",
            "event_datetime": "string",
            "event_receive_datetime": "string",
            "event_receive_timestamp": "integer",
            "event_timestamp": "integer",
            "is_reengagement": "string",
            "profile_id": "string",
            "publisher_id": "integer",
            "publisher_name": "string",
            "session_id": "integer",
            "tracker_name": "string",
            "tracking_id": "integer",
            "android_id": "string",
            "appmetrica_device_id": "string",
            "appmetrica_sdk_version": "integer",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "original_device_model": "string",
            "os_version": "string",
            "windows_aid": "string",
            "app_build_number": "integer",
            "app_package_name": "string",
            "app_version_name": "string",
        }
    },
    "push_tokens": {
        "fields": {
            "token": "string",
            "token_datetime": "string",
            "token_receive_datetime": "string",
            "token_receive_timestamp": "integer",
            "token_timestamp": "integer",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "os_name": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_package_name": "string",
            "app_version_name": "string",
            "application_id": "integer",
        }
    },
    "crashes": {
        "fields": {
            "crash": "string",
            "crash_datetime": "string",
            "crash_group_id": "integer",
            "crash_id": "integer",
            "crash_name": "string",
            "crash_receive_datetime": "string",
            "crash_receive_timestamp": "integer",
            "crash_timestamp": "integer",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "os_name": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_package_name": "string",
            "app_version_name": "string",
            "application_id": "integer",
        }
    },
    "errors": {
        "fields": {
            "error": "string",
            "error_datetime": "string",
            "error_id": "string",
            "error_name": "string",
            "error_receive_datetime": "string",
            "error_receive_timestamp": "integer",
            "error_timestamp": "integer",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "os_name": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_package_name": "string",
            "app_version_name": "string",
            "application_id": "integer",
        }
    },
    "sessions_starts": {
        "fields": {
            "session_id": "integer",
            "session_start_datetime": "string",
            "session_start_receive_datetime": "string",
            "session_start_receive_timestamp": "integer",
            "session_start_timestamp": "integer",
            "appmetrica_device_id": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "integer",
            "mnc": "integer",
            "operator_name": "string",
            "original_device_model": "string",
            "os_name": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_build_number": "integer",
            "app_package_name": "string",
            "app_version_name": "string",
            "application_id": "integer",
        }
    },
    "ecommerce_events":{
        "fields":{
            "ecom_type": "string",
            "ecom_screen_name": "string",
            "ecom_screen_search_query": "string",
            "ecom_screen_payload": "string",
            "ecom_screen_category_path_1":"string",
            "ecom_screen_category_path_2":"string",
            "ecom_screen_category_path_3":"string",
            "ecom_screen_category_path_4":"string",
            "ecom_screen_category_path_5":"string",
            "ecom_screen_category_path_6":"string",
            "ecom_screen_category_path_7":"string",
            "ecom_screen_category_path_8":"string",
            "ecom_screen_category_path_9":"string",
            "ecom_screen_category_path_10":"string",
            "ecom_product_name":"string",
            "ecom_product_sku":"string",
            "ecom_product_promocodes":"string",
            "ecom_product_payload":"string",
            "ecom_product_category_path_1":"string",
            "ecom_product_category_path_2":"string",
            "ecom_product_category_path_3":"string",
            "ecom_product_category_path_4":"string",
            "ecom_product_category_path_5":"string",
            "ecom_product_category_path_6":"string",
            "ecom_product_category_path_7":"string",
            "ecom_product_category_path_8":"string",
            "ecom_product_category_path_9":"string",
            "ecom_product_category_path_10":"string",
            "ecom_product_actual_price_fiat_unit_type":"string",
            "ecom_product_actual_price_fiat_value":"string",
            "ecom_product_actual_price_internal_components":"object",
            "ecom_product_original_price_fiat_unit_type":"string",
            "ecom_product_original_price_fiat_value":"string",
            "ecom_product_original_price_internal_components":"object",
            "ecom_cart_item_price_fiat_unit_type":"string",
            "ecom_cart_item_price_fiat_value":"string",
            "ecom_cart_item_quantity":"string",
            "ecom_cart_item_internal_components":"object",
            "ecom_referrer_type":"string",
            "ecom_referrer_id":"string",
            "ecom_order_id":"string",
            "ecom_order_payload":"string",
            "event_datetime":"string",
            "event_name":"string",
            "event_receive_datetime":"string",
            "event_receive_timestamp": "string",
            "event_timestamp": "string",
            "session_id":"string",
            "installation_id":"string",
            "certificate_verification_status": "string",
            "android_id": "string",
            "appmetrica_device_id": "string",
            "appmetrica_sdk_version": "string",
            "country": "string",
            "district": "string",
            "area": "string",
            "city": "string",
            "connection_type": "string",
            "country_iso_code": "string",
            "device_ipv6": "string",
            "device_locale": "string",
            "device_manufacturer": "string",
            "device_model": "string",
            "device_type": "string",
            "event_source": "string",
            "google_aid": "string",
            "ios_ifa": "string",
            "ios_ifv": "string",
            "mcc": "string",
            "mnc": "string",
            "operator_name": "string",
            "original_device_model": "string",
            "os_version": "string",
            "profile_id": "string",
            "windows_aid": "string",
            "app_build_number": "string",
            "app_package_name": "string",
            "app_version_name": "string",
        }
    }
}
