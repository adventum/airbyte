from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class EscrowAccountsListReport(BaseModel):
    commisioningObjectCode: Optional[str] = Field(description="Код очереди")
    commisioningObjectTitle: Optional[str] = Field(description="Название очереди")
    residentialComplex: Optional[str] = Field(description="Название ЖК")
    individualTermsId: Optional[str] = Field(description="ID индивидуальных условий")
    individualTermsStatus: Optional[str] = Field(description="Статус индивидуальных условий")
    escrowAccount: Optional[str] = Field(description="Номер счета эскроу")
    escrowAccountDate: Optional[date] = Field(description="Дата открытия счета")
    escrowAccountState: Optional[str] = Field(description="Состояние счета эскроу")
    escrowAccountCloseDate: Optional[date] = Field(description="Дата закрытия счета")
    escrowAmount: Optional[float] = Field(description="Депонируемая сумма")
    incomingBalance: Optional[float] = Field(description="Входящий остаток на начало периода (включительно)")
    outgoingBalance: Optional[float] = Field(description="Исходящий остаток на конец периода (не включительно)")
    expireDate: Optional[date] = Field(description="Дата завершения срока условного депонирования")
    depositor: Optional[str] = Field(description="Депонент")
    depositorTaxId: Optional[str] = Field(description="ИНН депонента")
    equityParticipationAgreementNumber: Optional[str] = Field(description="Номер ДДУ")
    equityParticipationAgreementDate: Optional[date] = Field(description="Дата ДДУ")
    authorizedRepresentative: Optional[str] = Field(description="ФИО доверенного лица")
    isConcession: Optional[bool] = Field(description="Признак уступки по договору")
    concessionDate: Optional[date] = Field(description="Дата уступки")
