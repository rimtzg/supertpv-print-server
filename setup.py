from setuptools import setup

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
      packages = ['supertpv-print-server',
      'supertpv-print-server.templates',
      'supertpv-print-server.static'],
)