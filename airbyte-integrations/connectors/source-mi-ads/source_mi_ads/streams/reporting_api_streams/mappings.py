from typing import Literal

AdType = Literal["Effect", "Brand"]
Dimension = Literal[
    "Campaign", "AdGroup", "Ad", "Country/Region", "Date", "AdPlacement", "Publisher"
]

ad_type_mapper: dict[AdType, int] = {"Effect": 1, "Brand": 2}

dimension_mapper: dict[Dimension, int] = {
    "Campaign": 1,
    "AdGroup": 2,
    "Ad": 3,
    "Country/Region": 4,
    "Date": 5,
    "AdPlacement": 9,
    "Publisher": 10,
}
