import setuptools

def get_long_description() -> str:
    with open('README.md') as fp:
        return fp.read()

setuptools.setup(
    name='mongomodel',
    version='0.1',
    scripts=[],
    author="Sébastien Nicolet",
    author_email="snicolet@student.42.fr",
    description="Tiny mongodb odm",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Chr0nos/mongorm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)