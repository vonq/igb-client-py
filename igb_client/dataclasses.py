import abc
from dataclasses import dataclass, field
from typing import Optional, Literal, List

from deepmerge import Merger
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


def _xml_tag_for_list_serialization(parent):
    if parent == "credentials":
        return "credential"
    if parent == "jobboards":
        return "jobboard"

    return "item"


class XMLSerializable:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def to_xml(self): raise NotImplementedError

    @abc.abstractmethod
    def asdict(self): raise NotImplementedError


@dataclass
class Credential(abc.ABC, XMLSerializable):
    credentials: dict
    destination: Literal["OFCCP", "MyContract"]

    def to_xml(self):
        return dicttoxml(self.asdict(),
                         custom_root=self.destination,
                         attr_type=False,
                         item_func=_xml_tag_for_list_serialization)


@dataclass
class ContractCredential(Credential):
    job_board: JobBoard = field(default_factory=JobBoard)
    destination = "MyContract"

    def asdict(self):
        return {
            "jobboards": [
                {
                    "class": self.job_board.klass,
                    "credentials": _to_igb_credential_pairs(self.credentials)
                }
            ]
        }


@dataclass
class ATSCredential(Credential):
    ats_id: str
    ats_name: str
    company_name: str
    company_id: str
    destination = "OFCCP"

    def asdict(self):
        return {
            "ATS": {
                "name": self.ats_name,
                "id": str(self.ats_id)
            },
            "company": {
                "name": self.company_name,
                "id": str(self.company_id),
                "credentials": [{"name": "", "value": ""}] if not self.credentials
                else [{"name": k, "value": v} for k, v in self.credentials.items()]
            }
        }


@dataclass
class OfccpCredential(XMLSerializable):
    ats: ATSCredential = field(default_factory=ATSCredential)
    job_board_contracts: List[ContractCredential] = field(default_factory=list)
    destination = "OFCCP"

    def to_xml(self):
        return dicttoxml(self.asdict(),
                         custom_root=self.destination,
                         attr_type=False,
                         item_func=_xml_tag_for_list_serialization)

    def asdict(self):
        final_dict = {}
        credential_merger = Merger(
            # pass in a list of tuple, with the strategies you are looking to apply to each type.
            type_strategies = [
                (list, ["append"]),
                (dict, ["merge"]),
                (set, ["union"])
            ],
            # next, choose the fallback strategies, applied to all other types:
            fallback_strategies=["override"],
            # finally, choose the strategies in the case where the types conflict:
            type_conflict_strategies=["override"]
        )
        credential_merger.merge(final_dict, self.ats.asdict())
        for jbc in self.job_board_contracts:
            credential_merger.merge(final_dict, jbc.asdict())

        return final_dict