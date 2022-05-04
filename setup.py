import setuptools

# Reads the content of your README.md into a variable to be used in the setup below
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name='saturated-places',                           # should match the package folder
    packages=['saturated-palces'],                     # should match the package folder
    version='0.0.1',                                # important for updates
    license='MIT',                                  # should match your chosen license
    description='Effeciently download Google Places API POI data for area within Polygon',
    long_description=long_description,              # loads your README.md
    long_description_content_type="text/markdown",  # README.md is of type 'markdown'
    author='Hisham Sajid',
    author_email='hishamsajid113@gmail.com',
    url='https://github.com/hishamsajid/saturated-places', 
    project_urls = {                                # Optional
        "Bug Tracker": "https://github.com/hishamsajid/saturated-places/issues"
    },
    install_requires=['requests'],                  # list all packages that your package uses
    keywords=["pypi", "saturated-places", "gis",'places api','poi'], #descriptive meta-data
    classifiers=[                                   # https://pypi.org/classifiers
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Documentation',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    
    download_url="https://github.com/mike-huls/toolbox_public/archive/refs/tags/0.0.3.tar.gz",
)