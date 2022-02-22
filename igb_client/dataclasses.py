from dataclasses import dataclass, field
from typing import Optional

from dicttoxml import dicttoxml


@dataclass
class JobBoard:
    name: str
    klass: str
    instructions: str
    logo: Optional[str] = None
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


@dataclass
class ATSCredential:
    ats_id: str
    ats_name: str
    company_name: str
    company_id: str
    credentials: dict

    def to_xml(self):
        return dicttoxml({
            "ATS": {
                "name": self.ats_name,
                "id": self.ats_id
            },
            "company": {
                "name": self.company_name,
                "id": self.company_id,
                "credentials": self.credentials
            }
        }, custom_root="OFCCP")
