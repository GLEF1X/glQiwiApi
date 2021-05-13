import pathlib

import setuptools

PATH = pathlib.Path(__file__).parent

README = (PATH / "README.md").read_text()

REQUIREMENTS = (PATH / "docs/requirements.txt").read_text()

setuptools.setup(
    packages=setuptools.find_packages(exclude=(
        'tests', 'examples', 'examples.*')
    ),
    name="glQiwiApi",  # Replace with your own username
    version="0.2.2",
    author="GLEF1X",
    author_email="glebgar567@gmail.com",
    description="Light and fast wrapper for test_qiwi and yoomoney",
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
