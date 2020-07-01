from setuptools import setup
from os import path

this_directory = path.abspath(path.dirname(__file__))
# with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
#     long_description = f.read()

packages = ['flask_tools']
print('packages=', packages)

setup(
    name="gm_flask_tools",

    version="1.1.30",
    # 1.1.30 - Bug fix in PathString
    # 1.1.16 - Added misfire_grace_time to ScheduleJob
    # 1.1.10 - Added APScheduler
    # 1.1.8 - Made OnExit public function
    # 1.1.7 - Bug fix in GetConfigVar
    # 1.1.5 - Added Echo url
    # 1.1.4 - Added Job logging
    # 1.1.3 - Added dictabase==* to pipfile
    # 1.1.1 - New feature: ScheduleJob()
    # 1.0.1 - bug fix. UserClass 'email' key forced to .lower()
    # 1.0.0 - init release to pypi

    packages=packages,
    install_requires=['flask', 'dictabase', 'requests', 'flask-apscheduler'],
    # scripts=['say_hello.py'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    # install_requires=['docutils>=0.3'],

    # package_data={
    #     # If any package contains *.txt or *.rst files, include them:
    #     '': ['*.txt', '*.rst'],
    #     # And include any *.msg files found in the 'hello' package, too:
    #     'hello': ['*.msg'],
    # },

    # metadata to display on PyPI
    author="Grant miller",
    author_email="grant@grant-miller.com",
    description="A collection of useful tools for developing web pages in python/flask",
    long_description="A collection of useful tools for developing web pages in python/flask",
    license="PSF",
    keywords="grant miller flask tools helpers",
    url="https://bitbucket.org/grant_miller/flask-tools",  # project home page, if any
    project_urls={
        "Source Code": "https://bitbucket.org/grant_miller/flask-tools/src/master/",
    }

    # could also include long_description, download_url, classifiers, etc.
)

# to push to PyPI

# python -m setup.py sdist bdist_wheel
# twine upload dist/*