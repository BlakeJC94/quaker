from setuptools import setup, find_packages

with open("README.md", 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="quaker",
    version='0.2.0',
    description="Lightweight python API to USGS earthquake dataset",
    long_description=long_description,
    author='BlakeJC94',
    author_email='blakejamescook@gmail.com',
    url='https://github.com/BlakeJC94/sudoku-py',
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "requests",
    ],
    # entry_points={
    #     'console_scripts': ['quaker=quaker.__main__:main'],
    # }
)

