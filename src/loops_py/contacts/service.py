from __future__ import annotations

from typing import Any, Dict, List, Mapping, Union

from ..core import LoopsCore
from ..models import (
    Contact,
    ContactProperty,
    ContactRequest,
    ContactUpsertResponse,
    CreateContactPropertyRequest,
    DeleteContactRequest,
    FindContactQuery,
    SuccessResponse,
    UpdateContactRequest,
)


class ContactsService:
    def __init__(self, core: LoopsCore) -> None:
        self._core = core

    def create_contact(
        self,
        request: Union[ContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[ContactUpsertResponse, Dict[str, Any]]:
        payload = self._core.validate_request(request, ContactRequest)
        result = self._core.request("POST", "/contacts/create", payload=payload)
        return self._core.marshal_single(result, ContactUpsertResponse, as_json)

    def update_contact(
        self,
        request: Union[UpdateContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[ContactUpsertResponse, Dict[str, Any]]:
        payload = self._core.validate_request(request, UpdateContactRequest)
        result = self._core.request("POST", "/contacts/update", payload=payload)
        return self._core.marshal_single(result, ContactUpsertResponse, as_json)

    def find_contact(
        self,
        query: Union[FindContactQuery, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[List[Contact], List[Dict[str, Any]]]:
        query_model = self._core.validate_request(query, FindContactQuery)
        result = self._core.request(
            "GET",
            "/contacts/find",
            query=self._core.to_payload(query_model),
        )
        return self._core.marshal_list(result, Contact, as_json)

    def delete_contact(
        self,
        request: Union[DeleteContactRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        payload = self._core.validate_request(request, DeleteContactRequest)
        result = self._core.request("POST", "/contacts/delete", payload=payload)
        return self._core.marshal_single(result, SuccessResponse, as_json)

    def create_contact_property(
        self,
        request: Union[CreateContactPropertyRequest, Mapping[str, Any]],
        *,
        as_json: bool | None = None,
    ) -> Union[SuccessResponse, Dict[str, Any]]:
        payload = self._core.validate_request(request, CreateContactPropertyRequest)
        result = self._core.request("POST", "/contacts/properties", payload=payload)
        return self._core.marshal_single(result, SuccessResponse, as_json)

    def list_contact_properties(
        self,
        *,
        list_type: str | None = None,
        as_json: bool | None = None,
    ) -> Union[List[ContactProperty], List[Dict[str, Any]]]:
        query = {"list": list_type} if list_type else None
        result = self._core.request("GET", "/contacts/properties", query=query)
        return self._core.marshal_list(result, ContactProperty, as_json)
