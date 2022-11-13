from setuptools import setup

setup(
    name="twistedfate",
    version="0.1.0",
    description="Bayes API Match wrapper",
    url="https://github.com/Bcastet/twistedfate",
    author='Benjamin Castet',
    author_email='benjamin.castet@gmail.com',
    license='BSD 2-clause',
    packages=['kayle', 'kayle/ddragon'],
    install_requires=["munch==2.5.0",
                      "pantheon==2.0.0",
                      "Pillow==9.3.0",
                      "pytest==7.2.0",
                      "requests==2.28.1",
                      "setuptools==65.5.0"],
)
