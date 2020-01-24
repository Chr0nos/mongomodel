import setuptools

def get_long_description() -> str:
    with open('README.md') as fp:
        return fp.read()

setuptools.setup(
    name='mongomodel',
    version='0.2.6',
    scripts=[],
    author="Sébastien Nicolet",
    author_email="snicolet@student.42.fr",
    description="Tiny mongodb odm, it mimics the orm of django",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/Chr0nos/mongorm",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=['pymongo>=3.9.0']
)
