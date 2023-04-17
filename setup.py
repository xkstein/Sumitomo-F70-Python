from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup (
    name='sumitomo_f70',
    version='0.0.1',
    author='Jamie Eckstein',
    packages=find_packages(),
    description='Unofficial Sumitomo F70 Helium Compressor python driver',
    long_description=long_description,
    long_description_content_type="text/markdown",
)
