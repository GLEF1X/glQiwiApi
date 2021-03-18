import setuptools

setuptools.setup(
    name="glparser2",  # Replace with your own username
    version="0.0.6",
    author="GLEF1X",
    author_email="glebgar567@gmail.com",
    description="Parser for post and get requests",
    long_description='Base queries',
    long_description_content_type="text/x-rst",
    url="https://github.com/GLEF1X/parser",
    packages=['glparser'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "aiohttp==3.7.3",
        "aiosocksy==0.1.2",
        "wheel",
    ],
    python_requires=">=3.6",
)
