# IGB Client for Python

This is a simple client and set of data classes used to interact with the IGB API.

# Contents

- `igb_client` project directory for the Python package. Note that its only content is the `package-project/src` directory for now. If you wanted to add tests or something you could put those in `package-project/tests` or something.
- `igb_client.client` Several Client classes used for sending credentials, listing job boards and listing and validating facet values.
- `igb_client.dataclasses` Several useful dataclasses to be used with the IGB client. Includes converting from credentials in `{k:v}` dict format to XML node structures accepted by the API.  
- `igb_client.encrypt` Contains AESCypher used for encrypting credentials (IGB SHOULD have the key to decrypt)   

# Example usage
coming soon