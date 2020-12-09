import os
from setuptools import setup

README = """
See the README on `GitHub
<https://github.com/uw-it-aca/retention-data-pipeline>`_.
"""

# The VERSION file is created by travis-ci, based on the tag name
version_path = "retention_data_pipeline/VERSION"
VERSION = open(os.path.join(os.path.dirname(__file__), version_path)).read()
VERSION = VERSION.replace("\n", "")

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

url = "https://github.com/uw-it-aca/retention-data-pipeline"
setup(
    name="Retention Analytics Dashboard Data Pipeline",
    version=VERSION,
    packages=["retention_data_pipeline"],
    author="UW-IT AXDD",
    author_email="aca-it@uw.edu",
    include_package_data=True,
    install_requires=[
        "Django>=2.2,<3.0",
        "UW-RestClients-SWS>=2.2.7,<3.0",
        "pyodbc<5",
        "pandas",
        "psycopg2",
        "UW-Django-SAML2",
        "requests",
        "python-crontab",
    ],
    license="Apache License, Version 2.0",
    description="A tool for interacting with retention analytics data",
    long_description=README,
    url=url,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
    ],
)
