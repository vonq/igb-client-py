import abc
from dataclasses import dataclass, field
from typing import Optional

from dicttoxml import dicttoxml


@dataclass
class JobBoard:
    name: str
    klass: str
    instructions: Optional[str] = None
    compliance: Optional[str] = None
    logo: Optional[str] = None
    classifications: Optional[list] = field(default_factory=list)
    moc: Optional[dict] = field(default_factory=dict)
    ofccp: Optional[dict] = field(default_factory=dict)
    options: Optional[list] = field(default_factory=list)
    facets: Optional[list] = field(default_factory=list)

    def __str__(self):
        return self.klass

    @property
    def pk(self):
        return self.klass


@dataclass
class BoardFacet:
    key: str
    label: str


def _to_igb_credential_pairs(credentials: dict):
    return [{"name": k, "value": v} for k, v in credentials.items()]


@dataclass
class Credential(abc.ABC):
    credentials: dict

    @abc.abstractmethod
    def to_xml(self):
        pass


@dataclass
class ContractCredential(Credential):
    job_board: JobBoard = field(default_factory=JobBoard)

    def to_xml(self):
        return dicttoxml({
            "jobboards": [
                {
                    "jobboard": {
                        "class": self.job_board.klass,
                        "credentials": _to_igb_credential_pairs(self.credentials)
                    },
                }
            ]
        }, custom_root="MyContract", attr_type=False)


@dataclass
class ATSCredential(Credential):
    ats_id: str
    ats_name: str
    company_name: str
    company_id: str

    def to_xml(self):
        return dicttoxml({
            "ATS": {
                "name": self.ats_name,
                "id": str(self.ats_id)
            },
            "company": {
                "name": self.company_name,
                "id": str(self.company_id),
                "credentials": self.credentials
            }
        }, custom_root="OFCCP", attr_type=False)
