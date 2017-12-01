from distutils.core import setup

NAME = "supertpv-print-server"
VERSION = "0.1dev"
DESCRIPTION = 'Print Server of SuperTPV'
AUTHOR = "Rimtzg"
EMAIL = "rimtzg@gmail.com"
URL = "https://www.supertpv.com"

setup(name = NAME,
      version = VERSION,
      description = DESCRIPTION,
      author = AUTHOR,
      author_email = EMAIL,
      url = URL,
      include_package_data=True,
      packages = ['supertpv-print-server',
      'supertpv-print-server.templates',
      'supertpv-print-server.static'],
      license='LICENSE.txt',
      long_description=open('README.txt').read(),
      install_requires=[
        "Flask",
        "flask_httpauth",
        "gunicorn",
        "pymongo",
        "python-escpos",
    ],
)