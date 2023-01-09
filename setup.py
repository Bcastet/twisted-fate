from setuptools import setup

setup(
    name="nidalee",
    version="0.1.8",
    description="Bayes API Match wrapper",
    url="https://github.com/Bcastet/twisted-fate",
    author='Benjamin Castet',
    author_email='benjamin.castet@gmail.com',
    license='BSD 2-clause',
    packages=['nidalee', 'nidalee/assets'],
    install_requires=["kayle",
                      "munch==2.5.0",
                      "Pillow==9.3.0",
                      "requests==2.28.1"],
    include_package_data=True
)
