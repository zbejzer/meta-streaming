from setuptools import setup

setup(
    name="metastreaming",
    version="0.2.0",
    packages=["metastreaming"],
    entry_points={"console_scripts": ["metastreaming = metastreaming.__main__:main"]},
)
