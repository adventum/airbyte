import re
import xml.etree.ElementTree as ET
from datetime import date
from typing import Optional, List
from typing import Type, Mapping, Any, Iterable
from uuid import uuid4

from airbyte_cdk.models import SyncMode
from airbyte_cdk.sources.streams import Stream
from pydantic import BaseModel

from source_sber_escrow.auth import TokenAuthenticator
from source_sber_escrow.schemas.escrow_accounts_list import EscrowAccountsListReport
from source_sber_escrow.schemas.escrow_accounts_transactions import EscrowAccountsTransactionReport
from source_sber_escrow.types import SberCredentials, IsSuccess, Message
from source_sber_escrow.utils import CertifiedRequests


def get_commission_object_codes(
    token: str,
    client_id: str,
    sber_client_cert: Optional[str] = None,
    sber_client_key: Optional[str] = None,
    sber_ca_chain: Optional[str] = None,
) -> list[str]:
    certified_request = CertifiedRequests(client_cert=sber_client_cert, client_key=sber_client_key, ca_chain=sber_ca_chain)

    url = "https://api.sberbank.ru:8443/prod/tradefin/escrow/v2/residential-complex"
    headers = {
        "authorization": f"Bearer {token}",
        "x-ibm-client-id": client_id,
        "x-introspect-rquid": uuid4().hex,
    }
    response = certified_request.get(url, headers=headers)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    ns = {"ns": "http://model.tfido.escrow.sbrf.ru"}

    codes = []
    for complex_elem in root.findall("ns:residentialComplex", ns):
        for comm_obj_elem in complex_elem.findall("ns:commissioningObject", ns):
            code_elem = comm_obj_elem.find("ns:code", ns)
            if code_elem is not None and code_elem.text:
                codes.append(code_elem.text)

    print(f"Commissioning object codes: {codes}")
    return codes


def check_sber_escrow_connection(
    credentials: SberCredentials,
    sber_client_cert: Optional[str] = None,
    sber_client_key: Optional[str] = None,
    sber_ca_chain: Optional[str] = None,
) -> tuple[IsSuccess, Optional[Message]]:
    try:
        get_commission_object_codes(
            token=credentials.access_token.get_secret_value(),
            client_id=credentials.client_id,
            sber_client_cert=sber_client_cert,
            sber_client_key=sber_client_key,
            sber_ca_chain=sber_ca_chain,
        )
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
        sber_client_cert: Optional[str] = None,
        sber_client_key: Optional[str] = None,
        sber_ca_chain: Optional[str] = None,
    ):
        self.credentials = credentials
        self.date_from = date_from
        self.date_to = date_to
        self.sber_client_cert = sber_client_cert
        self.sber_client_key = sber_client_key
        self.sber_ca_chain = sber_ca_chain

        self._authenticator = TokenAuthenticator(
            client_id=self.credentials.client_id,
            client_secret=self.credentials.client_secret,
            sber_client_cert=self.sber_client_cert,
            sber_client_key=self.sber_client_key,
            sber_ca_chain=self.sber_ca_chain,
        )
        self._certified_request = CertifiedRequests(
            client_cert=self.sber_client_cert, client_key=self.sber_client_key, ca_chain=self.sber_ca_chain
        )

    @property
    def primary_key(self) -> None:
        return None

    def get_headers(self) -> dict:
        return {
            "authorization": f"Bearer {self._fetch_token()}",
            "content-type": "application/x-www-form-urlencoded",
            "x-ibm-client-id": self.credentials.client_id,
            "x-introspect-rquid": uuid4().hex,
        }

    def create_request_body(self) -> dict:
        commisioning_object_codes = get_commission_object_codes(
            token=self._fetch_token(),
            client_id=self.credentials.client_id,
            sber_client_cert=self.sber_client_cert,
            sber_client_key=self.sber_client_key,
            sber_ca_chain=self.sber_ca_chain,
        )
        return {
            "сommisioningObjectCode": commisioning_object_codes,
            "startReportDate": self.date_from.isoformat(),
            "endReportDate": self.date_to.isoformat(),
            "limit": 9999,
            "offset": 0,
        }

    def get_json_schema(self) -> Mapping[str, Any]:
        return self.SCHEMA.schema()

    def read_records(
        self,
        sync_mode: SyncMode,
        cursor_field: List[str] = None,
        stream_slice: Mapping[str, Any] = None,
        stream_state: Mapping[str, Any] = None,
    ) -> Iterable[Mapping[str, Any]]:
        response = self._certified_request.post(url=self.URL, headers=self.get_headers(), data=self.create_request_body())
        response.raise_for_status()
        yield from self._parse_xml_response(resp=response.text)

    def _parse_xml_response(self, resp: str) -> Iterable[Mapping[str, Any]]:
        raise NotImplementedError

    def _fetch_token(self) -> str:
        return self._authenticator().access_token.get_secret_value()


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
