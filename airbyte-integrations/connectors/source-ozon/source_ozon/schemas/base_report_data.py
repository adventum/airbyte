from __future__ import annotations

from datetime import date, datetime
from typing import Sequence, Optional

from pydantic import BaseModel, Field, validator


class BaseOzonReport(BaseModel):
    date_den: Optional[date] = Field(description="Дата", alias="День")
    date_data: Optional[date] = Field(description="Дата", alias="Дата")

    @property
    def date(self) -> Optional[date]:
        return self.date_den or self.date_data

    @classmethod
    def from_list_of_values(cls, values: Sequence) -> "BaseOzonReport":
        return cls.parse_obj(dict(zip(cls.__fields__.keys(), values)))

    @validator("date_den", "date_data", pre=True)
    def parse_date_field(cls, value: str | date | datetime) -> date:
        if isinstance(value, str):
            return datetime.strptime(value, "%d.%m.%Y")
        return value
