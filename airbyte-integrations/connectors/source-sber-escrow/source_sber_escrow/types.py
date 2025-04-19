from datetime import date
from typing import Optional

from pydantic import BaseModel, SecretStr


class SberCredentials(BaseModel):
    access_token: SecretStr
    client_id: str
    client_secret: str
    client_cert: Optional[str] = None
    client_key: Optional[str] = None
    ca_chain: Optional[str] = None


IsSuccess = bool
Message = str
StartDate = date
EndDate = date
