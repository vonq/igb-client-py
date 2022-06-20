from typing import Dict, Set
from .parse_custom import params_extra_parser


ROOT_FIELDS_CUSTOM_EXTRACT = {"params": params_extra_parser}


def parse_igb_xml_payload(payload: Dict) -> Dict:
    """
    IGB's JSON payload is a weird XML->JSON conversion, which converts
        <elements>
            <element>1</element>
            <element>2</element>
        </elements>

    Into

        "elements": {
            "element": 1,
            "element": 2.
        }

    So we need a function to recursively traverse that JSON to reformat it in a sensible way
    """
    if not isinstance(payload, dict):
        # end condition
        return payload

    for key in list(payload.keys()):
        if key.lower() in ["facets", "credentials", "options", "params", "rules"]:
            # only a few tags are containers in IGB's XSD
            singular_key = key.rstrip("s")
            if not payload.get(key):
                continue
            # extract additional fields that would be overwritten/lost by next iteration
            if key in ROOT_FIELDS_CUSTOM_EXTRACT:
                payload.update(ROOT_FIELDS_CUSTOM_EXTRACT[key](payload))
            payload[key] = [
                parse_igb_xml_payload(item[singular_key])
                for item in payload[key]
                if singular_key in item
            ]
        else:
            payload[key] = parse_igb_xml_payload(payload[key])
    return payload
