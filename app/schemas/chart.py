from pydantic import BaseModel
from typing import Dict, List


class ChartData(BaseModel):
    data: Dict[str, List[int]]

    class Config:
        schema_extra = {
            "example": {
                "data": {
                    "label1": [1, 2, 3, 4],
                    "label2": [5, 6, 7]
                }
            }
        }
