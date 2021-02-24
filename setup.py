from setuptools import setup, find_packages

setup(
    name="fluss",
    version="0.0.1",
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'fluss-organizer = fluss.apps.organizer.main:entry',
        ],
    },
)
