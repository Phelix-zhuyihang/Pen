from setuptools import setup

setup(
    name="pen",
    version="1.0.0",
    description="NetCut 粘贴板命令行工具",
    author="Pen CLI",
    packages=[],
    install_requires=[
        "requests>=2.31.0",
        "click>=8.1.7",
        "colorama>=0.4.6"
    ],
    entry_points={
        "console_scripts": [
            "pen = pen:cli",
        ]
    },
)
