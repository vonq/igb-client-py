from typing import Dict


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

    for key, value in payload.items():
        if key.lower() in ["facets", "credentials", "options", "params", "rules"]:
            # only a few tags are containers in IGB's XSD
            singular_key = key.rstrip("s")
            if not payload.get(key):
                continue
            payload[key] = [
                parse_igb_xml_payload(item[singular_key]) for item in payload[key]
            ]
        else:
            payload[key] = parse_igb_xml_payload(payload[key])
    return payload