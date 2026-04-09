from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="csv-to-text-formatter",
    version="1.0.0",
    author="csv-to-text-formatter contributors",
    description="A CSV-to-text formatter using pandas and Jinja2 templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Runvargr/csv-to-text-formatter-",
    packages=find_packages(exclude=["tests*", "examples*"]),
    include_package_data=True,
    package_data={
        "csv_formatter": ["templates/*.j2"],
    },
    install_requires=requirements,
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "csv-formatter=csv_formatter.cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
