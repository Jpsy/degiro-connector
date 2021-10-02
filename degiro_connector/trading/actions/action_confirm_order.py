# IMPORTATION STANDARD
import requests
import logging
from typing import Any, Dict, Optional, Union

# IMPORTATION THIRD PARTY
from google.protobuf import json_format

# IMPORTATION INTERNAL
import degiro_connector.core.constants.urls as urls
from degiro_connector.trading.models.trading_pb2 import (
    Credentials,
    Order,
)
from degiro_connector.core.abstracts.abstract_action import AbstractAction


class ActionConfirmOrder(AbstractAction):
    ORDER_FILTER_MATCHING = {
        Order.OrderType.LIMIT: {
            "buySell",
            "orderType",
            "price",
            "productId",
            "size",
            "timeType",
        },
        Order.OrderType.STOP_LIMIT: {
            "buySell",
            "orderType",
            "price",
            "productId",
            "size",
            "stopPrice",
            "timeType",
        },
        Order.OrderType.MARKET: {
            "buySell",
            "orderType",
            "productId",
            "size",
            "timeType",
        },
        Order.OrderType.STOP_LOSS: {
            "buySell",
            "orderType",
            "productId",
            "size",
            "stopPrice",
            "timeType",
        },
    }

    @classmethod
    def order_to_api(cls, order: Order) -> Dict[str, Union[float, int, str]]:
        # Build dict from message
        order_dict = json_format.MessageToDict(
            message=order,
            including_default_value_fields=True,
            preserving_proto_field_name=False,
            use_integers_for_enums=True,
            descriptor_pool=None,
            float_precision=None,
        )

        # Setup 'buySell'
        if order.action == order.Action.BUY:
            order_dict["buySell"] = "BUY"
        else:
            order_dict["buySell"] = "SELL"

        # Filter fields
        fields_to_keep = set()
        if order.order_type in cls.ORDER_FILTER_MATCHING:
            fields_to_keep = cls.ORDER_FILTER_MATCHING[order.order_type]
        else:
            raise AttributeError("Invalid `OrderType`.")

        filtered_order_dict = dict()
        for field in order_dict.keys() & fields_to_keep:
            filtered_order_dict[field] = order_dict[field]

        return filtered_order_dict

    @staticmethod
    def confirmation_response_to_grpc(
        payload: dict,
    ) -> Order.ConfirmationResponse:
        confirmation_response = Order.ConfirmationResponse()
        confirmation_response.response_datetime.GetCurrentTime()
        json_format.ParseDict(
            js_dict=payload["data"],
            message=confirmation_response,
            ignore_unknown_fields=False,
            descriptor_pool=None,
        )

        return confirmation_response

    @classmethod
    def confirm_order(
        cls,
        confirmation_id: str,
        credentials: Credentials,
        order: Order,
        session_id: str,
        logger: logging.Logger = None,
        raw: bool = False,
        session: requests.Session = None,
    ) -> Union[Order.ConfirmationResponse, Dict[Any, Any], None]:
        if logger is None:
            logger = cls.build_logger()
        if session is None:
            session = cls.build_session()

        int_account = credentials.int_account
        url = urls.ORDER_CONFIRM
        url = f"{url}/{confirmation_id};jsessionid={session_id}"

        params = {
            "intAccount": int_account,
            "sessionId": session_id,
        }

        order_dict = cls.order_to_api(order=order)

        request = requests.Request(
            method="POST",
            url=url,
            json=order_dict,
            params=params,
        )
        prepped = session.prepare_request(request)
        response_raw = None

        try:
            response_raw = session.send(prepped, verify=False)
            response_dict = response_raw.json()
        except Exception as e:
            logger.fatal(response_raw)
            logger.fatal(e)
            return None

        if (
            isinstance(response_dict, dict)
            and "data" in response_dict
            and "orderId" in response_dict["data"]
        ):
            if raw is True:
                order.id = response_dict["data"]["orderId"]
                response = response_dict
            else:
                order.id = response_dict["data"]["orderId"]
                response = cls.confirmation_response_to_grpc(
                    payload=response_dict,
                )
        else:
            response = None

        return response

    def call(
        self,
        confirmation_id: str,
        order: Order,
        raw: bool = False,
    ) -> Union[Order.ConfirmationResponse, Dict[Any, Any], None]:
        connection_storage = self.connection_storage
        session_id = connection_storage.session_id
        credentials = self.credentials
        session = self.session_storage.session
        logger = self.logger

        return self.confirm_order(
            confirmation_id=confirmation_id,
            credentials=credentials,
            order=order,
            session_id=session_id,
            logger=logger,
            raw=raw,
            session=session,
        )