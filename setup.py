import pathlib

import setuptools

PATH = pathlib.Path(__file__).parent

README = (PATH / "README.md").read_text()

REQUIREMENTS = (PATH / "SETUP_REQUIREMENTS.txt").read_text()

setuptools.setup(
    packages=setuptools.find_packages(exclude=(
        'tests', 'examples', 'examples.*', 'tests', 'tests.*')
    ),
    name="glQiwiApi",  # Replace with your own username
    version="1.0.0",
    author="GLEF1X",
    author_email="glebgar567@gmail.com",
    description="Light and fast wrapper of QIWI and YooMoney api's",
    package_data={"glQiwiApi": ["py.typed", "*.pyi", "**/*.pyi"]},
    # Длинное описание, которое будет отображаться на странице PyPi.
    # Использует README.md репозитория для заполнения.
    long_description=README,
    # Определяет тип контента, используемый в long_description.
    long_description_content_type="text/markdown",
    license="MIT",
    url="https://github.com/GLEF1X/glQiwiApi",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
    ],
    install_requires=REQUIREMENTS,
    python_requires=">=3.7",
)
