from setuptools import setup

setup(
    name="pen",
    version="1.7.0",
    description="NetCut 粘贴板命令行工具",
    author="Pen CLI",
    py_modules=["pen"],
    install_requires=[
        "requests>=2.31.0",
        "click>=8.1.7",
        "colorama>=0.4.6",
        "charset-normalizer>=3.4.0",
        "pyperclip>=1.9.0",
    ],
    entry_points={
        "console_scripts": [
            "pen = pen:cli",
        ],
    },
)
