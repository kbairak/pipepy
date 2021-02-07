from setuptools import find_packages, setup

setup(name="pipepy",
      version="0.0.1",
      packages=find_packages("src"),
      package_dir={'': "src"})
