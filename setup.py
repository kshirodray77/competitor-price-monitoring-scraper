from setuptools import setup, find_packages

setup(
    name="price-tracker",
    version="1.0.0",
    description="Competitor price monitoring tool with email alerts",
    author="Kshirod",
    author_email="ray.kshirod@gmail.com",
    url="https://github.com/kshirodray77/competitor-price-monitoring-scraper",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "PyYAML>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "price-tracker=src.main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
