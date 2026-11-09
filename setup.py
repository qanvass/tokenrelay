from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="tokenrelay",
    version="2.2.0",
    description="The intelligent orchestrator that routes IDE tasks to the best, cheapest models.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TokenRelay Core Architecture Team",
    url="https://github.com/your-org/tokenrelay",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "tokenrelay=tokenopt.cli:main",
            "tokenopt=tokenopt.cli:main",
        ],
    },
)
