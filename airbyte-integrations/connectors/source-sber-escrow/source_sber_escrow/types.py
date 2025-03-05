from __future__ import annotations

from datetime import date

from pydantic import BaseModel, SecretStr


class SberCredentials(BaseModel):
    access_token: SecretStr
    client_id: str
    client_cert: str | None
    client_key: str | None
    ca_chain: str | None


IsSuccess = bool
Message = str
StartDate = date
EndDate = date
