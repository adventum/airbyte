#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import json
import socket
import re
from typing import Dict, Generator, Mapping

from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.models.airbyte_protocol import (
    AirbyteCatalog,
    AirbyteConnectionStatus,
    AirbyteMessage,
    ConfiguredAirbyteCatalog,
    Status,
    Type,
)
from airbyte_cdk.sources.source import Source
from apiclient import errors
from requests.status_codes import codes as status_codes
from unidecode import unidecode

from .client import GoogleSheetsClient
from .helpers import Helpers, logger
from .models.spreadsheet import Spreadsheet
from .models.spreadsheet_values import SpreadsheetValues
from .auth import CredentialsCraftAuthenticator

# set default batch read size
ROW_BATCH_SIZE = 200
# override default socket timeout to be 10 mins instead of 60 sec.
# on behalf of https://github.com/airbytehq/oncall/issues/242
DEFAULT_SOCKET_TIMEOUT: int = 600
socket.setdefaulttimeout(DEFAULT_SOCKET_TIMEOUT)


class GoogleSheetsSource(Source):
    """
    Spreadsheets API Reference: https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets
    """

    def __init__(self):
        super().__init__()
        self.field_name_map: dict[str, str] | None = None
        self.field_name_map_stream: dict[str, str] | None = None

    def check(self, logger: AirbyteLogger, config: json) -> AirbyteConnectionStatus:
        # Check involves verifying that the specified spreadsheet is reachable with our credentials.
        try:
            if config["credentials"]["auth_type"] == "credentials_craft_auth":
                client = GoogleSheetsClient(self.get_credentials(config)["credentials"])
            else:
                client = GoogleSheetsClient(self.get_credentials(config))
        except Exception as e:
            return AirbyteConnectionStatus(status=Status.FAILED, message=f"Please use valid credentials json file. Error: {e}")

        # logger.info(config)
        spreadsheets = config.get("spreadsheets")
        for spreadsheet_id in spreadsheets:
            spreadsheet_id = spreadsheet_id["spreadsheet_id"]
            # logger.info("##"*20)
            # logger.info(spreadsheets)
            # logger.info(spreadsheet_id)
            # logger.info("##"*20)

            # Replace part of spreadsheet_id if placeholder in spreadsheet_id
            if self.contains_placeholder(spreadsheet_id):
                path_placeholder = config["path_placeholder"]
                spreadsheet_id = spreadsheet_id.replace("{placeholder}", path_placeholder)

            spreadsheet_id = Helpers.get_spreadsheet_id(spreadsheet_id)

            try:
                # Attempt to get first row of sheet
                client.get(spreadsheetId=spreadsheet_id, includeGridData=False, ranges="1:1")
            except errors.HttpError as err:
                reason = str(err)
                # Give a clearer message if it's a common error like 404.
                if err.resp.status == status_codes.NOT_FOUND:
                    reason = "Requested spreadsheet was not found."
                logger.error(f"Formatted error: {reason}")
                return AirbyteConnectionStatus(
                    status=Status.FAILED, message=f"Unable to connect with the provided credentials to spreadsheet. Error: {reason}"
                )

            # Check for duplicate headers
            spreadsheet_metadata = Spreadsheet.parse_obj(client.get(spreadsheetId=spreadsheet_id, includeGridData=False))

            grid_sheets = Helpers.get_grid_sheets(spreadsheet_metadata)

            duplicate_headers_in_sheet = {}
            for sheet_name in grid_sheets:
                print(f"Это check {sheet_name}")
                try:
                    header_row_data = Helpers.get_first_row(client, spreadsheet_id, sheet_name)
                    print(f"Это check {header_row_data}")
                    _, duplicate_headers = Helpers.get_valid_headers_and_duplicates(header_row_data)
                    if duplicate_headers:
                        duplicate_headers_in_sheet[sheet_name] = duplicate_headers
                except Exception as err:
                    if str(err).startswith("Expected data for exactly one row for sheet"):
                        logger.warn(f"Skip empty sheet: {sheet_name}")
                    else:
                        logger.error(str(err))
                        return AirbyteConnectionStatus(
                            status=Status.FAILED, message=f"Unable to read the schema of sheet {sheet_name}. Error: {str(err)}"
                        )
            if duplicate_headers_in_sheet:
                duplicate_headers_error_message = ", ".join(
                    [
                        f"[sheet:{sheet_name}, headers:{duplicate_sheet_headers}]"
                        for sheet_name, duplicate_sheet_headers in duplicate_headers_in_sheet.items()
                    ]
                )
                return AirbyteConnectionStatus(
                    status=Status.FAILED,
                    message="The following duplicate headers were found in the following sheets. Please fix them to continue: "
                    + duplicate_headers_error_message,
                )

            return AirbyteConnectionStatus(status=Status.SUCCEEDED)

    def discover(self, logger: AirbyteLogger, config: json) -> AirbyteCatalog:
        if config["credentials"]["auth_type"] == "credentials_craft_auth":
            client = GoogleSheetsClient(self.get_credentials(config)["credentials"])
        else:
            client = GoogleSheetsClient(self.get_credentials(config))

        streams = []
        spreadsheets = config.get("spreadsheets")
        for spreadsheet_id in spreadsheets:
            spreadsheet_id = spreadsheet_id["spreadsheet_id"]

            # Replace part of spreadsheet_id if placeholder in spreadsheet_id
            if self.contains_placeholder(spreadsheet_id):
                path_placeholder = config["path_placeholder"]
                spreadsheet_id = spreadsheet_id.replace("{placeholder}", path_placeholder)

            spreadsheet_id = Helpers.get_spreadsheet_id(spreadsheet_id)
            try:
                self.field_name_map = self.get_field_name_map(config=config)
                self.field_name_map_stream = self.get_field_name_map_stream(
                    config=config,
                    spreadsheet_id=spreadsheet_id
                )

                logger.info(f"Running discovery on sheet {spreadsheet_id}")
                spreadsheet_metadata = Spreadsheet.parse_obj(client.get(spreadsheetId=spreadsheet_id, includeGridData=False))
                grid_sheets = Helpers.get_grid_sheets(spreadsheet_metadata)

                for sheet_name in grid_sheets:
                    try:
                        header_row_data = Helpers.get_first_row(client, spreadsheet_id, sheet_name)
                        sheet_name = self.translate_name(self.field_name_map_stream.get(sheet_name, sheet_name))

                        header_row_data = [self.field_name_map.get(col, col) for col in header_row_data]
                        stream = Helpers.headers_to_airbyte_stream(logger, sheet_name, header_row_data)
                        streams.append(stream)
                    except Exception as err:
                        if str(err).startswith("Expected data for exactly one row for sheet"):
                            logger.warn(f"Skip empty sheet: {sheet_name}")
                        else:
                            logger.error(str(err))

            except errors.HttpError as err:
                reason = str(err)
                if err.resp.status == status_codes.NOT_FOUND:
                    reason = "Requested spreadsheet was not found."
                raise Exception(f"Could not run discovery: {reason}")

        return AirbyteCatalog(streams=streams)

    def read(
            self, logger: AirbyteLogger, config: json, catalog: ConfiguredAirbyteCatalog, state: Dict[str, any]
    ) -> Generator[AirbyteMessage, None, None]:
        if config["credentials"]["auth_type"] == "credentials_craft_auth":
            client = GoogleSheetsClient(self.get_credentials(config)["credentials"])
        else:
            client = GoogleSheetsClient(self.get_credentials(config))

        spreadsheets = config.get("spreadsheets")
        duplicate = {} # Contains pair {duplicate: unique} sheets
        unique = {}
        for spreadsheet_id in spreadsheets:
            spreadsheet_id = spreadsheet_id["spreadsheet_id"]

            # Replace part of spreadsheet_id if placeholder in spreadsheet_id
            if self.contains_placeholder(spreadsheet_id):
                path_placeholder = config["path_placeholder"]
                spreadsheet_id = spreadsheet_id.replace("{placeholder}", path_placeholder)

            spreadsheet_id = Helpers.get_spreadsheet_id(spreadsheet_id)

            available_sheets = Helpers.get_sheets_in_spreadsheet(client, spreadsheet_id)

            old_fields = self.get_field_name_map(config=config)
            renamed_sheets = self.get_field_name_map_stream(config=config, spreadsheet_id=spreadsheet_id)

            # Добавление исходных названий листов, для их транслитерации
            for available_sheet in available_sheets:
                if available_sheet in renamed_sheets.keys():
                    continue
                else:
                    origin_sheet_for_transliterate = {available_sheet: available_sheet}
                    renamed_sheets.update(origin_sheet_for_transliterate)

            renamed_sheets = {key: self.translate_name(value) for key, value in renamed_sheets.items()}
            sheet_to_column_name = Helpers.parse_sheet_and_column_names_from_catalog(catalog)
            new_to_old_names = {new: old for old, new in old_fields.items()}

            restored_sheet_to_column_name = {}
            for sheet, columns in sheet_to_column_name.items():
                restored_columns = frozenset(new_to_old_names.get(column, column) for column in columns)
                restored_sheet_to_column_name[sheet] = restored_columns

            logger.info(f"Starting syncing spreadsheet {spreadsheet_id}")

            sheet_to_column_index_to_name = Helpers.get_available_sheets_to_column_index_to_name(
                client, spreadsheet_id, restored_sheet_to_column_name, renamed_sheets
            )

            # logger.info(f"Sheet_to_column_index_to_name_keys: {sheet_to_column_index_to_name.keys()}")
            # logger.info(f"Sheet_to_column_index_to_name_values: {sheet_to_column_index_to_name.values()}")
            sheet_row_counts = Helpers.get_sheet_row_count(client, spreadsheet_id)
            # logger.info(f"Row counts: {sheet_row_counts}")

            # Union duplicates sheets
            # logger.info(f"sheet_to_column_index_to_name (Name_of_sheet: dict(index: [column_names])) - {sheet_to_column_index_to_name}")

            for sheet, columns in sheet_to_column_name.items():
                if sheet_to_column_name[sheet] not in unique.values():
                    unique[sheet] = columns
                else:
                    unique_sheet_with_same_value = None
                    for key, value in unique.items():
                        if columns == value:
                            unique_sheet_with_same_value = key
                    duplicate[sheet] = unique_sheet_with_same_value

            for original_sheet in sheet_to_column_index_to_name.keys():
                logger.info(f"Syncing sheet {original_sheet}")
                column_index_to_name = sheet_to_column_index_to_name[original_sheet]

                for key, value in column_index_to_name.items():
                    if value in old_fields.keys():
                        column_index_to_name[key] = old_fields[value]

                row_cursor = 2  # we start syncing after the title line
                while row_cursor <= sheet_row_counts[original_sheet]:
                    range = f"{original_sheet}!{row_cursor}:{row_cursor + ROW_BATCH_SIZE}"
                    logger.info(f"Fetching range {range}")
                    row_batch = SpreadsheetValues.parse_obj(
                        client.get_values(spreadsheetId=spreadsheet_id, ranges=range, majorDimension="ROWS")
                    )

                    row_cursor += ROW_BATCH_SIZE + 1
                    value_ranges = row_batch.valueRanges[0]

                    if not value_ranges.values:
                        break

                    row_values = value_ranges.values
                    if len(row_values) == 0:
                        break

                    for row in row_values:
                        if not Helpers.is_row_empty(row) and Helpers.row_contains_relevant_data(row, column_index_to_name.keys()):
                            sheet = renamed_sheets.get(original_sheet, original_sheet)
                            if duplicate:
                                sheet = duplicate.get(sheet, sheet)
                            yield AirbyteMessage(type=Type.RECORD, record=Helpers.row_data_to_record_message(sheet, row, column_index_to_name))
            logger.info(f"Finished syncing spreadsheet {spreadsheet_id}")

    @staticmethod
    def get_credentials(config):
        # backward compatible with old style config
        if config.get("credentials_json"):
            credentials = {"auth_type": "Service", "service_account_info": config.get("credentials_json")}
            return credentials

        credentials = config.get("credentials")
        auth_type = credentials.get("auth_type")

        if auth_type == "credentials_craft_auth":
            authenticator = CredentialsCraftAuthenticator(
                credentials_craft_host=credentials["credentials_craft_host"],
                credentials_craft_token=credentials["credentials_craft_token"],
                credentials_craft_token_id=credentials["credentials_craft_token_id"]
            )
            return {"auth_type": "Client", "credentials": authenticator.token}

        return credentials

    @staticmethod
    def get_field_name_map(config: Mapping[str, any]) -> dict[str, str]:
        """Get values that needs to be replaced and their replacements"""
        field_name_map: list[dict[str, str]] | None
        if not (field_name_map := config.get("field_name_map")):
            return {}
        else:
            return {item["old_value"]: item["new_value"] for item in field_name_map}

    @staticmethod
    def get_field_name_map_stream(config: Mapping[str, any], spreadsheet_id: str) -> dict[str, str]:
        """Get values that needs to be replaced and their replacements for specific spreadsheet"""
        for spreadsheet in config.get("spreadsheets", []):
            if spreadsheet_id in spreadsheet.get("spreadsheet_id"):
                field_name_map_stream = spreadsheet.get("field_name_map_stream", [])
                return {item["old_value_stream"]: item["new_value_stream"] for item in field_name_map_stream}
        return {}

    @staticmethod
    def contains_placeholder(file_path: str) -> bool:
        return "{placeholder}" in file_path

    @staticmethod
    def contains_date_placeholder(file_path: str) -> str:
        # Returns a format like %Y-%m-%d
        searching_pattern = r'!(.*?)!'
        is_match = re.search(searching_pattern, file_path)

        if is_match:
            extracted_string = is_match.group(1)
            return extracted_string

    @staticmethod
    def translate_name(name: str):
        name = re.sub("[^A-Za-z0-9\s]+", "", unidecode(name))
        name = name.strip()
        name = re.sub("[\s]", "_", name)
        name = re.sub("_{2,}", "_", name)
        return name.lower()
