from setuptools import setup, find_packages

setup(
    name="bookforge",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[],  # Only uses Python standard library
    entry_points={
        "console_scripts": [
            "bookforge=bookforge.cli:main",
            "bf=bookforge.cli:main",  # Also support short alias 'bf'
        ],
    },
    package_data={
        "bookforge": ["prompts/**/*.md"],
    },
    python_requires=">=3.8",
)
