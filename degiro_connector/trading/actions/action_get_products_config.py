# IMPORTATION STANDARD
import logging
from typing import Dict, Union

# IMPORTATION THIRD PARTY
import requests
from google.protobuf import json_format

# IMPORTATION INTERNAL
import degiro_connector.core.constants.urls as urls
from degiro_connector.core.abstracts.abstract_action import AbstractAction
from degiro_connector.trading.models.trading_pb2 import (
    Credentials,
    ProductSearch,
)


class ActionGetProductsConfig(AbstractAction):
    @staticmethod
    def products_config_to_grpc(payload: dict) -> ProductSearch.Config:
        products_config = ProductSearch.Config()
        json_format.ParseDict(
            js_dict={"values": payload},
            message=products_config,
            ignore_unknown_fields=False,
            descriptor_pool=None,
        )

        return products_config

    @classmethod
    def get_products_config(
        cls,
        session_id: str,
        credentials: Credentials,
        raw: bool = False,
        session: requests.Session = None,
        logger: logging.Logger = None,
    ) -> Union[dict, ProductSearch.Config]:
        """Fetch the product search config table.
        No credentials or logging seems to be required for this endpoint.
        Just adding the credentials and session_id because the website is
        doing it.
        Args:
            session_id (str):
                API's session id.
            credentials (Credentials):
                Credentials containing the parameter "int_account".
            raw (bool, optional):
                Whether are not we want the raw API response.
                Defaults to False.
            session (requests.Session, optional):
                This object will be generated if None.
                Defaults to None.
            logger (logging.Logger, optional):
                This object will be generated if None.
                Defaults to None.
        Returns:
            ProductSearch.Config: API response.
        """

        if logger is None:
            logger = cls.build_logger()
        if session is None:
            session = cls.build_session()

        int_account = credentials.int_account
        url = urls.PRODUCTS_CONFIG

        params = {
            "intAccount": int_account,
            "sessionId": session_id,
        }

        request = requests.Request(method="GET", url=url, params=params)
        prepped = session.prepare_request(request)
        response_raw = None

        try:
            response_raw = session.send(prepped, verify=False)
            response_dict = response_raw.json()

            if raw is True:
                response = response_dict
            else:
                response = cls.products_config_to_grpc(
                    payload=response_dict,
                )
        except Exception as e:
            logger.fatal(response_raw)
            logger.fatal(e)
            return None

        return response

    def call(
        self,
        raw: bool = False,
    ) -> Union[dict, ProductSearch.Config]:
        connection_storage = self.connection_storage
        session_id = connection_storage.session_id
        session = self.session_storage.session
        credentials = self.credentials
        logger = self.logger

        return self.get_products_config(
            session_id=session_id,
            credentials=credentials,
            raw=raw,
            session=session,
            logger=logger,
        )