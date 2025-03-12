import re
import xml.etree.ElementTree as ET
from datetime import date
from datetime import datetime, timedelta
from typing import Optional, List
from typing import Type, Mapping, Any, Iterable
from uuid import uuid4

from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources.streams import Stream
from pydantic import BaseModel

from source_sber_escrow.schemas.escrow_accounts_list import EscrowAccountsListReport
from source_sber_escrow.schemas.escrow_accounts_transactions import EscrowAccountsTransactionReport
from source_sber_escrow.types import SberCredentials, IsSuccess, Message
from source_sber_escrow.utils import CertifiedRequests


def check_sber_escrow_connection(
    credentials: SberCredentials,
    commisioning_object_codes: Optional[list[str]] = None,
    individual_terms_id: Optional[list[str]] = None,
    sber_client_cert: Optional[str] = None,
    sber_client_key: Optional[str] = None,
    sber_ca_chain: Optional[str] = None,
) -> tuple[IsSuccess, Optional[Message]]:
    certified_request = CertifiedRequests(client_cert=sber_client_cert, client_key=sber_client_key, ca_chain=sber_ca_chain)

    data = {
        "startReportDate": (datetime.now() - timedelta(days=2)).date().isoformat(),
        "endReportDate": (datetime.now() - timedelta(days=1)).date().isoformat(),
        "limit": 1,
        "offset": 0,
    }

    if commisioning_object_codes:
        data["сommisioningObjectCode"] = commisioning_object_codes
    elif individual_terms_id:
        data["individualTermsId"] = individual_terms_id
    else:
        return False, "No commissioning object codes or individual terms IDs provided"

    try:
        response = certified_request.post(
            url="https://api.sberbank.ru:8443/prod/tradefin/escrow/v2/account-oper-list",
            headers={
                "authorization": f"Bearer {credentials.access_token.get_secret_value()}",
                "content-type": "application/x-www-form-urlencoded",
                "x-ibm-client-id": credentials.client_id,
                "x-introspect-rquid": uuid4().hex,
            },
            data=data,
        )
        response.raise_for_status()
        return True, None
    except Exception as e:
        print(f"Sber-Escrow connection check failed: {str(e)}")
        return False, str(e)


class BaseEscrowAccountsStream(Stream):
    URL: str = NotImplemented
    SCHEMA: Type[BaseModel] = NotImplemented

    def __init__(
        self,
        credentials: SberCredentials,
        date_from: date,
        date_to: date,
        commisioning_object_codes: Optional[list[str]] = None,
        individual_terms_id: Optional[list[str]] = None,
        sber_client_cert: Optional[str] = None,
        sber_client_key: Optional[str] = None,
        sber_ca_chain: Optional[str] = None,
    ):
        self.credentials = credentials
        self.date_from = date_from
        self.date_to = date_to
        self.commisioning_object_codes = commisioning_object_codes
        self.individual_terms_id = individual_terms_id
        self.sber_client_cert = sber_client_cert
        self.sber_client_key = sber_client_key
        self.sber_ca_chain = sber_ca_chain

        self._certified_request = CertifiedRequests(
            client_cert=self.sber_client_cert, client_key=self.sber_client_key, ca_chain=self.sber_ca_chain
        )

    @property
    def primary_key(self) -> None:
        return None

    @property
    def headers(self) -> dict:
        return {
            "authorization": f"Bearer {self.credentials.access_token.get_secret_value()}",
            "content-type": "application/x-www-form-urlencoded",
            "x-ibm-client-id": self.credentials.client_id,
            "x-introspect-rquid": uuid4().hex,
        }

    @property
    def data(self) -> dict:
        data = {
            "startReportDate": self.date_from.isoformat(),
            "endReportDate": self.date_to.isoformat(),
            "limit": 9999,
            "offset": 0,
        }

        if self.commisioning_object_codes:
            data["сommisioningObjectCode"] = self.commisioning_object_codes
        elif self.individual_terms_id:
            data["individualTermsId"] = self.individual_terms_id
        else:
            raise ValueError("No commissioning object codes or individual terms IDs provided")

        return data

    def get_json_schema(self) -> Mapping[str, Any]:
        return self.SCHEMA.schema()

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        response = self._certified_request.post(url=self.URL, headers=self.headers, data=self.data)
        response.raise_for_status()
        yield from self._parse_xml_response(resp=response.text)

    def _parse_xml_response(self, resp: str) -> Iterable[Mapping[str, Any]]:
        raise NotImplementedError


class EscrowAccountsListStream(BaseEscrowAccountsStream):
    URL: str = "https://api.sberbank.ru:8443/prod/tradefin/escrow/v2/account-list"
    SCHEMA: Type[EscrowAccountsListReport] = EscrowAccountsListReport

    def _parse_xml_response(self, resp: str) -> Iterable[Mapping[str, Any]]:
        xml_content = re.search(r"<\?xml.*</escrowAccountList>", resp, re.DOTALL)
        if not xml_content:
            raise ValueError("XML content not found in HTTP response")

        xml_str = xml_content.group(0)
        namespace = {"ns": "http://model.tfido.escrow.sbrf.ru"}
        root = ET.fromstring(xml_str)

        for account_elem in root.findall("./ns:escrowAccount", namespace):
            account_data = {}

            for child in account_elem:
                tag = child.tag.split("}")[-1]
                text = child.text or ""

                if tag in [
                    "escrowAccountDate",
                    "escrowAccountCloseDate",
                    "expireDate",
                    "equityParticipationAgreementDate",
                    "concessionDate",
                ]:
                    account_data[tag] = date.fromisoformat(text) if text.strip() else None
                elif tag in ["escrowAmount", "incomingBalance", "outgoingBalance"]:
                    account_data[tag] = float(text) if text.strip() else None
                elif tag == "isConcession":
                    account_data[tag] = text.lower() == "true" if text.strip() else None
                else:
                    account_data[tag] = text if text.strip() else None

            yield self.SCHEMA(**account_data).dict()


class EscrowAccountsTransactionStream(BaseEscrowAccountsStream):
    URL: str = "https://api.sberbank.ru:8443/prod/tradefin/escrow/v2/account-oper-list"
    SCHEMA: Type[EscrowAccountsTransactionReport] = EscrowAccountsTransactionReport

    def _parse_xml_response(self, resp: str) -> Iterable[Mapping[str, Any]]:
        xml_content = re.search(r"<\?xml.*</escrowAccountOperationList>", resp, re.DOTALL)
        if not xml_content:
            raise ValueError("XML content not found in HTTP response")

        xml_str = xml_content.group(0)
        namespace = {"ns": "http://model.tfido.escrow.sbrf.ru"}
        root = ET.fromstring(xml_str)

        for operation_elem in root.findall("./ns:escrowAccountOperation", namespace):
            operation_data = {}

            for child in operation_elem:
                tag = child.tag.split("}")[-1]
                text = child.text or ""

                if tag == "operationDate":
                    operation_data[tag] = date.fromisoformat(text) if text.strip() else None
                elif tag == "operationSum":
                    operation_data[tag] = float(text) if text.strip() else None
                elif tag == "isExpenseOperation":
                    operation_data[tag] = text.lower() == "true" if text.strip() else None
                else:
                    operation_data[tag] = text if text.strip() else None

            yield self.SCHEMA(**operation_data).dict()
