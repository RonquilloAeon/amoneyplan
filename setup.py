from setuptools import setup, find_packages

VERSION = "0.1.0"

setup(
    name="amoneyplan",
    version=VERSION,
    install_requires=[
        "pydantic==1.10.13",
        "python-ulid==1.1.0"
    ],
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.10",
    url="https://github.com/RonquilloAeon/amoneyplan",
)
