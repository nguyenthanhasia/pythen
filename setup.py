from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="pythen",
    version="0.2.0a3",
    description="Extensible Python framework for defeasible reasoning",
    long_description=Path(__file__).with_name("README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author="PYTHEN Contributors",
    url="https://github.com/nguyenthanhasia/pythen",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        # Optional engine for pythen.solvers.z3_native. The ctypes fallback
        # works with any Z3 5.x shared library; apt libz3 4.8.x is rejected
        # by the capability probe (see docs/z3_backend.md).
        "z3": ["z3-solver>=4.8.15"],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)
