from typing import Mapping, Any, MutableMapping


from .base import Bitrix24CrmStream


class Users(Bitrix24CrmStream):
    primary_key = "ID"

    def path(self, *args, **kwargs) -> str:
        return "user.get"

    def request_params(
        self, next_page_token: Mapping[str, Any] = None, **kwargs
    ) -> MutableMapping[str, Any]:
        params = super().request_params(next_page_token=next_page_token, **kwargs)
        params.update(
            {"FILTERS[USER_TYPE]": "employee"}
        )  # filter is required by task description
        return params
