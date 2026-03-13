from setuptools import setup, find_packages

setup(
    name='devops-cli',
    version='1.0.0',
    packages=find_packages(),
    py_modules=['cli', 'helpers'],
    install_requires=[
        'click',
        'rich',
        'tabulate',
        'pyyaml',
        'requests',
        'boto3',
    ],
    entry_points={
        'console_scripts': [
            'devops-cli=cli:cli',
        ],
    },
)
