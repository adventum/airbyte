from __future__ import annotations

from typing import Optional

from pydantic import Field, validator

from source_ozon.schemas.base_report_data import BaseOzonReport


class VideoBannerReport(BaseOzonReport):
    banner_id: Optional[str] = Field(description="ID баннера", alias="ID баннера")
    visible_impressions_iab: Optional[int] = Field(description="Видимые показы IAB", alias="Видимые показы IAB")
    impressions: Optional[int] = Field(description="Показы", alias="Показы")
    clicks: Optional[int] = Field(description="Клики", alias="Клики")
    coverage: Optional[float] = Field(description="Охват", alias="Охват")
    ctr: Optional[float] = Field(description="CTR", alias="CTR")
    visible_impressions_percentage: Optional[float] = Field(description="Доля видимых показов", alias="Доля видимых показов")
    views_until_the_end_by_quartile_25: Optional[float] = Field(description="Досмотры по квартилям 25%", alias="Досмотры по квартилям 25%")
    views_until_the_end_by_quartile_50: Optional[float] = Field(description="Досмотры по квартилям 50%", alias="Досмотры по квартилям 50%")
    views_until_the_end_by_quartile_75: Optional[float] = Field(description="Досмотры по квартилям 75%", alias="Досмотры по квартилям 75%")
    views_until_the_end_by_quartile_100: Optional[float] = Field(description="Досмотры по квартилям 100%", alias="Досмотры по квартилям 100%")
    views_percentage_25: Optional[float] = Field(description="Доля досмотров 25%", alias="Доля досмотров 25%")
    views_percentage_50: Optional[float] = Field(description="Доля досмотров 50%", alias="Доля досмотров 50%")
    views_percentage_75: Optional[float] = Field(description="Доля досмотров 75%", alias="Доля досмотров 75%")
    views_percentage_100: Optional[float] = Field(description="Доля досмотров 100%", alias="Доля досмотров 100%")
    views_with_sound: Optional[int] = Field(description="Просмотры со звуком", alias="Просмотры со звуком")
    orders: Optional[int] = Field(description="Заказы", alias="Заказы")
    expenses: Optional[float] = Field(description="Расход", alias="Расход")

    @validator(
        "coverage",
        "ctr",
        "visible_impressions_percentage",
        "views_until_the_end_by_quartile_25",
        "views_until_the_end_by_quartile_50",
        "views_until_the_end_by_quartile_75",
        "views_until_the_end_by_quartile_100",
        "views_percentage_25",
        "views_percentage_50",
        "views_percentage_75",
        "views_percentage_100",
        "expenses",
        pre=True,
    )
    def parse_float_field(cls, value: str | int | float | None) -> float | None:
        if not value:
            return
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value)
