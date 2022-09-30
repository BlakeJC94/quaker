from setuptools import setup

with open("README.md", 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="quaker",
    version='0.0.0',
    description="Lightweight python API to USGS earthquake dataset",
    long_description=long_description,
    author='BlakeJC94',
    author_email='blakejamescook@gmail.com',
    url='https://github.com/BlakeJC94/sudoku-py',
    python_requires=">=3.7",
    entry_points={
        'console_scripts': ['sudoku=sudoku_py.__main__:main'],
    }
)

