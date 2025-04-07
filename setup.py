from setuptools import setup, find_packages

setup(
    name="liquid_energy",
    version="0.1.0",
    description="Algorithmic market making bot for energy assets",
    author="Liquid Energy Team",
    author_email="info@liquid-energy.com",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    install_requires=[
        "hummingbot>=0.46.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "websockets>=10.0",
        "gym>=0.20.0",
        "torch>=1.9.0",
        "scikit-learn>=0.24.2",
    ],
    extras_require={
        "test": [
            "pytest>=6.2.5",
            "pytest-cov>=2.12.1",
            "pytest-asyncio>=0.18.0",
        ],
        "dev": [
            "flake8>=3.9.0",
            "mypy>=0.812",
        ],
    },
    python_requires=">=3.8",
)
