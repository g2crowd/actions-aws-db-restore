from setuptools import find_packages, setup

setup(
    name="db_restore",
    version="1.0",
    description="A Python package to restore RDS DB snapshot",
    author="Saurabh Jambhule",
    author_email="sjambhule@g2.com",
    packages=find_packages(include=["src", "src.*", "src", "src.*"]),
    install_requires=[
        "attrs==23.1.0; python_version >= '3.7'",
        "boto3==1.26.9",
        "botocore==1.29.9",
        "jmespath==1.0.1",
        "jsonschema==4.17.3",
        "pyrsistent==0.19.3; python_version >= '3.7'",
        "python-dateutil==2.8.2",
        "s3transfer==0.6.0",
        "setuptools==67.6.1",
        "six==1.16.0",
        "urllib3==1.26.12",
    ],
)
