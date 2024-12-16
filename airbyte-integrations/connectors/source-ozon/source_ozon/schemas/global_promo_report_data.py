from __future__ import annotations

from typing import Optional

from pydantic import Field, validator

from source_ozon.schemas.base_report_data import BaseOzonReport


class GlobalPromoReport(BaseOzonReport):
    banner: Optional[str] = Field(description="Название баннера", alias="Название баннера")
    impressions: Optional[int] = Field(description="Показы", alias="Показы")
    clicks: Optional[int] = Field(description="Клики", alias="Клики")
    ctr: Optional[float] = Field(description="CTR (%)", alias="CTR (%)")
    coverage: Optional[float] = Field(description="Охват", alias="Охват")
    avg_price_for_1000_impressions_rub: Optional[float] = Field(description="Ср. цена 1000 показов, ₽", alias="Ср. цена 1000 показов, ₽")
    expense_rub_with_vat: Optional[float] = Field(description="Расход, ₽, с НДС", alias="Расход, ₽, с НДС")

    @validator("ctr", "coverage", "avg_price_for_1000_impressions_rub", "expense_rub_with_vat", pre=True)
    def parse_float_field(cls, value: str | int | float | None) -> float | None:
        if not value:
            return
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
