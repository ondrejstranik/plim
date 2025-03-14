import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="plim",
    version="0.0.1",
    author="OndrejStranik",
    author_email="ondra.stranik@gmail.com",
    description="package for plasmon imaging",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ondrejstranik/viscope",
    packages = setuptools.find_packages(),
    install_requires = [
        'numpy',
        'PyQt5',
        'napari',
        'pytest',
        'pyserial'
        #'spectralCamera @ git+ssh://git@github.com/ondrejstranik/spectralCamera.git',
        #'viscope @ git+ssh://git@github.com/ondrejstranik/viscope.git',
        ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
)