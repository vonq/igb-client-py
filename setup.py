from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Python Client for IGB'

# Setting up
setup(
    name="igb_client",
    version=VERSION,
    author="VONQ",
    author_email="<development@vonq.com>",
    description=DESCRIPTION,
    packages=find_packages(),
    python_requires='>3.9.0',
    install_requires=[
        "pycryptodome>=3.11.0<3.12.0",
        "requests~=2.26.0",
        "requests_cache~=0.9.1"
    ],

)