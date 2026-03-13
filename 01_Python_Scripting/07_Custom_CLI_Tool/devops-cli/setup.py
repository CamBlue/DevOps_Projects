from setuptools import setup

setup(
    name='devops-cli',
    version='1.0.0',
    py_modules=['cli'],
    install_requires=[
        'click',
        'rich',
        'tabulate',
        'pyyaml',
        'requests'
    ],
    entry_points={
        'console_scripts': [
            'devops-cli=cli:cli',
        ],
    },
)