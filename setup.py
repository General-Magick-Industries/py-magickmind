from setuptools import setup, find_packages

setup(
    name="super_brain",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[],
    author="GMI",
    author_email="minoak@globalmagicko.com",
    description="A package for the Super Brain project",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/General-Magick-Industries/AGD_Super_Brain",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.10',
)