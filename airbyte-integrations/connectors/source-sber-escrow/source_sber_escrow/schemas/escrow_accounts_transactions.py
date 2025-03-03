from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EscrowAccountsTransactionReport(BaseModel):
    individualTermsId: Optional[str] = Field(description="ID индивидуальных условий")
    commisioningObjectCode: Optional[str] = Field(description="Код очереди")
    operationDate: Optional[date] = Field(description="Дата операции")
    operationSum: Optional[float] = Field(description="Сумма операции")
    isExpenseOperation: Optional[bool] = Field(
        description="Признак расходной операции (при поступлении средств на счет - false, при оттоке средств со счета - true)"
    )
