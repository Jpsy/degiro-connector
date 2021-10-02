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
    Agenda,
)


class ActionGetAgenda(AbstractAction):
    @staticmethod
    def agenda_request_to_api(
        request: Agenda.Request,
    ) -> dict:
        request_dict = json_format.MessageToDict(
            message=request,
            including_default_value_fields=False,
            preserving_proto_field_name=False,
            use_integers_for_enums=True,
            descriptor_pool=None,
            float_precision=None,
        )
        request_dict["calendarType"] = (
            Agenda.CalendarType.Name(request.calendar_type).title().replace("_", "")
        )
        request_dict["offset"] = request.offset
        request_dict["orderByDesc"] = request.order_by_desc

        return request_dict

    @staticmethod
    def agenda_to_grpc(
        request: Agenda.Request,
        payload: dict,
    ) -> Agenda:
        agenda = Agenda()
        agenda.response_datetime.GetCurrentTime()
        agenda.calendar_type = request.calendar_type
        json_format.ParseDict(
            js_dict=payload,
            message=agenda,
            ignore_unknown_fields=True,
            descriptor_pool=None,
        )

        return agenda

    @classmethod
    def get_agenda(
        cls,
        request: Agenda.Request,
        session_id: str,
        credentials: Credentials,
        raw: bool = False,
        session: requests.Session = None,
        logger: logging.Logger = None,
    ) -> Union[dict, Agenda]:
        if logger is None:
            logger = cls.build_logger()
        if session is None:
            session = cls.build_session()

        url = urls.AGENDA
        params = cls.agenda_request_to_api(
            request=request,
        )
        params["intAccount"] = credentials.int_account
        params["sessionId"] = session_id

        req = requests.Request(method="GET", url=url, params=params)
        prepped = session.prepare_request(req)
        response_raw = None

        try:
            response_raw = session.send(prepped, verify=False)
            response_dict = response_raw.json()

            if raw is True:
                response = response_dict
            else:
                response = cls.agenda_to_grpc(
                    request=request,
                    payload=response_dict,
                )
        except Exception as e:
            logger.fatal(response_raw)
            logger.fatal(e)
            return None

        return response

    def call(
        self,
        request: Agenda.Request,
        raw: bool = False,
    ) -> Union[dict, Agenda]:
        connection_storage = self.connection_storage
        session_id = connection_storage.session_id
        session = self.session_storage.session
        credentials = self.credentials
        logger = self.logger

        return self.get_agenda(
            request=request,
            session_id=session_id,
            credentials=credentials,
            raw=raw,
            session=session,
            logger=logger,
        )