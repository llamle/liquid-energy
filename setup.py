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
        "hummingbot",
        "numpy",
        "pandas",
        "pytest",
        "pytest-cov",
        "gym",
        "torch",
        "scikit-learn",
    ],
    python_requires=">=3.8",
)