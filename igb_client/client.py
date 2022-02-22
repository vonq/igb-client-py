from typing import List, Dict, Optional

from igb_client.dataclasses import JobBoard
from igb_client.encrypt import AESCypher
from igb_client.parse import parse_igb_xml_payload


class IGBClientBase:
    _instance = None
    base_url = "https://api.ingoedebanen.nl/apipartner/hapi/v1/{environment_id}/"
    credentials_storage_key = None

    def __init__(self, api_key: str, environment_id: str):
        self._environment_id = environment_id

        self.session = requests_cache.CachedSession('hapi_ofccp_cache')
        self.session.headers.update({
            "X-IGB-Api-Key": api_key
        })

    def __new__(cls, api_key: str, environment_id: str):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.__init__(api_key, environment_id)
        return cls._instance


class IGBCredentials(IGBClientBase):
    def post(self) ->bool:
        resp = self.session.post(
            self.base_url.format(environment_id=self._environment_id),
            data={}
        )
class IGBJobBoards(IGBClientBase):
    def list(self) -> Optional[List[JobBoard]]:
        resp = self.session.get(
            self.base_url.format(environment_id=self._environment_id),
        )
        if resp.ok:
            job_boards = resp.json()["HAPI"]["jobboards"]
            return [
                JobBoard(
                    name=job_board["jobboard"].get("name"),
                    klass=job_board["jobboard"].get("class"),
                    logo=job_board["jobboard"].get("logo"),
                )
                for job_board in job_boards
            ]

    def detail(self, job_board: str) -> Optional[JobBoard]:
        resp = self.session.get(f"/{job_board}")
        if resp.ok:
            job_board = resp.json()["HAPI"]["jobboard"]
            if job_board:
                job_board = parse_igb_xml_payload(job_board)
                return JobBoard(
                    name=job_board.get("name"),
                    klass=job_board.get("class"),
                    moc=job_board.get("MOC"),
                    instructions=job_board.get("instructions"),
                    ofccp=job_board.get("OFCCP"),
                    facets=job_board.get("facets"),
                )


class IGBFacets(IGBClientBase):
    def get_board_facets(
        self, job_board: str, facet_name: str, credentials: dict, term: str = None
    ) -> List[Dict]:
        autocomplete_url = (
            self.base_url.format(environment_id=self._environment_id)
            + f"/{job_board}/facet/{facet_name}/custom"
        )
        params = {
            k: AESCypher(self.credentials_storage_key).encrypt(v)
            for k, v in credentials.items()
        }

        if term:
            params["term"] = term

        resp = self.session(
            autocomplete_url,
            json={"params": params},
        )

        if resp.ok:
            return [
                {"key": item["key"], "label": item["label"]}
                for item in parse_igb_xml_payload(resp.json()).get("options", [])
            ]
        return []

    def validate(
        self, job_board: str, facet_name: str, credentials: dict, keys: list
    ) -> bool:
        validate_url = (
            self.base_url.format(environment_id=self._environment_id)
            + f"/{job_board}/facet/{facet_name}/custom/validate"
        )

        params = {
            k: AESCypher(self.credentials_storage_key).encrypt(v)
            for k, v in credentials.items()
        }

        params["keys"] = [{"key": key} for key in keys]

        resp = self.session.post(
            validate_url,
            json={"params": params},
        )

        if resp.ok:
            return resp.json().get("valid", False)
        return False
