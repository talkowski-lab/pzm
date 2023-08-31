from setuptools import setup, find_packages

# Read the contents of requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="pzm_filter",
    version="0.1",
    description="A Python package for filtering PZM variations.",
    packages=find_packages(),
    install_requires=requirements,
)
