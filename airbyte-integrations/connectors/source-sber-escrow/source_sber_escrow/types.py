from datetime import date

from pydantic import BaseModel, SecretStr


class SberCredentials(BaseModel):
    access_token: SecretStr
    client_id: str


IsSuccess = bool
Message = str
StartDate = date
EndDate = date
