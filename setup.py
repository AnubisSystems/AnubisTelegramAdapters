from setuptools import setup, find_packages

setup(
    name="AnubisTelegramAdapters",
    version="0.0.9",
    author="Jose Manuel Herera Saenz",
    author_email="incubadoradepollos@gmail.com",
    description="Core for Anubis System",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AnubisSystems/AnubisTelegramAdapters",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Intended Audience :: Education",
        "Intended Audience :: Developers",
        "Intended Audience :: Legal Industry",
        "Topic :: Education",
    ],
    python_requires=">=3.13.0",
    install_requires=[
         "python-telegram-bot",
         "AnubisCore @ git+https://github.com/AnubisSystems/AnubisCore.git"
    ],
)
