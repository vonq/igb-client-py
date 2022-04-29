import base64
import copy
from datetime import timedelta, datetime
from typing import List, Dict, Optional, Union, Type, TypeVar

import requests_cache

from igb_client.dataclasses import (
    JobBoard,
    ContractCredential,
    Credential,
    OfccpCredential,
    XMLSerializable,
)
from igb_client.encrypt import AESCypher
from igb_client.parse import parse_igb_xml_payload

CredentialInterface = TypeVar("CredentialInterface", bound=Credential)

IGB_URL = "https://api.ingoedebanen.nl/apipartner/hapi/v1"


class IGBClientError(Exception):
    pass


class IGBClientBase:
    _instance = None
    _base_url = "{base_url}/{environment_id}/{view}"
    _credentials_storage_key = None
    _credentials_transport_key = None

    def __init__(
        self,
        api_key: str,
        environment_id: str,
        credentials_storage_key: str,
        credentials_transport_key: str,
        base_url=IGB_URL,
        expire_after: Union[None, int, float, str, datetime, timedelta] = -1,
    ):
        self._environment_id = environment_id
        self._credentials_storage_key = credentials_storage_key
        self._credentials_transport_key = credentials_transport_key
        self._base_url = self._base_url.format(
            base_url=base_url, environment_id=environment_id, view="{view}"
        )

        self.session = requests_cache.CachedSession(
            f"igb_client_{environment_id}", expire_after=expire_after
        )
        self.session.headers.update({"X-IGB-Api-Key": api_key})

    def __new__(
        cls,
        api_key: str,
        environment_id: str,
        credentials_storage_key: str,
        credentials_transport_key: str,
        base_url=IGB_URL,
        expire_after: Union[None, int, float, str, datetime, timedelta] = -1,
    ):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(
                api_key,
                environment_id,
                credentials_storage_key,
                credentials_transport_key,
                base_url,
                expire_after,
            )
        return cls._instance

    def encrypt_credentials(
        self, decrypted_credentials: Type[CredentialInterface]
    ) -> Type[CredentialInterface]:
        credentials = copy.deepcopy(decrypted_credentials)
        credentials.credentials = {
            k: AESCypher(self._credentials_storage_key).encrypt(v)
            for k, v in credentials.credentials.items()
        }
        return credentials

    def decrypt_credentials(
        self, encrypted_credentials: Type[CredentialInterface]
    ) -> Type[CredentialInterface]:
        credentials = copy.deepcopy(encrypted_credentials)
        cipher = AESCypher(self._credentials_storage_key)
        credentials.credentials = {
            k: base64.b64decode(cipher.decrypt(v)).decode()
            for k, v in credentials.credentials.items()
        }
        return credentials

    def transport_credentials(
        self, decrypted_credentials: Type[CredentialInterface]
    ) -> Type[CredentialInterface]:
        credentials = copy.deepcopy(decrypted_credentials)
        cipher = AESCypher(self._credentials_transport_key)
        credentials.credentials = {
            k: cipher.encrypt(v) for k, v in credentials.credentials.items()
        }
        return credentials


class IGBCredentials(IGBClientBase):
    def post(self, decrypted_credentials: Type[XMLSerializable]) -> bool:
        if isinstance(decrypted_credentials, OfccpCredential):
            decrypted_credentials: OfccpCredential
            decrypted_credentials.ats = self.transport_credentials(
                decrypted_credentials.ats
            )
            decrypted_credentials.job_board_contracts = [
                self.transport_credentials(jbc)
                for jbc in decrypted_credentials.job_board_contracts
            ]
            resp = self.session.post(
                self._base_url.format(view="credentials"),
                data=decrypted_credentials.to_xml(),
            )
        elif issubclass(type(decrypted_credentials), Credential):
            decrypted_credentials: Credential
            resp = self.session.post(
                self._base_url.format(view="credentials"),
                data=self.transport_credentials(decrypted_credentials).to_xml(),
            )
        else:
            raise ValueError(f"Unsupported type '{type(decrypted_credentials)}'")
        if resp.ok:
            return True
        return False


class IGBJobBoards(IGBClientBase):
    def list(self) -> Optional[List[JobBoard]]:
        resp = self.session.get(
            self._base_url.format(view="jobboards"),
        )
        if not resp.ok:
            raise IGBClientError(
                f"Could not get jobboard list, http responde code: {resp.status_code}"
            )

        job_boards = resp.json()["HAPI"]["jobboards"]
        return [
            JobBoard(
                name=job_board["jobboard"].get("name"),
                klass=job_board["jobboard"].get("class"),
                logo=job_board["jobboard"].get("logo"),
                compliance=job_board["jobboard"].get("compliance"),
                classifications=job_board["jobboard"].get("classifications"),
            )
            for job_board in job_boards
        ]

    def detail(self, job_board: str) -> Optional[JobBoard]:
        resp = self.session.get(self._base_url.format(view=f"jobboards/{job_board}"))
        if not resp.ok:
            raise IGBClientError(
                f"Could not get jobboard detail, http responde code: {resp.status_code}"
            )

        job_board = resp.json()["HAPI"]["jobboard"]
        if job_board:
            job_board = parse_igb_xml_payload(job_board)
            return JobBoard(
                name=job_board.get("name"),
                klass=job_board.get("class"),
                moc=job_board.get("MOC"),
                instructions=job_board.get("instructions"),
                ofccp=job_board.get("OFCCP"),
                classifications=job_board.get("OFCCP", {}).get("classifications"),
                facets=job_board.get("facets"),
            )


class IGBFacets(IGBClientBase):
    def get_board_facets(
        self,
        credentials: Optional[ContractCredential],
        facet_name: str,
        term: str = None,
    ) -> List[Dict]:
        autocomplete_url = self._base_url.format(
            view=f"jobboards/{credentials.job_board.klass}/facet/{facet_name}/custom"
        )

        params = {}

        if credentials:
            params = self.encrypt_credentials(credentials).credentials

        if term:
            params["term"] = term

        resp = self.session.post(
            autocomplete_url,
            json={"params": params},
        )

        if not resp.ok:
            raise IGBClientError(
                f"Could not get board facets, http responde code: {resp.status_code}"
            )

        return [
            {"key": item["key"], "label": item["label"]}
            for item in parse_igb_xml_payload(resp.json()).get("options", [])
        ]

    def validate(
        self, credentials: ContractCredential, facet_name: str, keys: list
    ) -> bool:
        validate_url = self._base_url.format(
            view=f"jobboards/{credentials.job_board.klass}/facet/{facet_name}/custom/validate"
        )

        params = self.encrypt_credentials(credentials).credentials

        params["keys"] = [{"key": key} for key in keys]

        resp = self.session.post(
            validate_url,
            json={"params": params},
        )

        if not resp.ok:
            raise IGBClientError(
                f"Could not validate, http responde code: {resp.status_code}"
            )

        return resp.json().get("valid", False)
