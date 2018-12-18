from os.path import dirname, abspath, join
from setuptools import setup

with open(abspath(join(dirname(__file__), 'README.rst'))) as fileobj:
    README = fileobj.read().strip()

install_reqs = [req for req in open(abspath(join(dirname(__file__), 'requirements.txt')))]

setup(
    name='bullock',
    description='Distributed lock using Redis',
    long_description=README,
    author='Juarez Bochi',
    author_email='jbochi+github@gmail.com',
    version='1.0.0',
    include_package_data=True,
    install_requires=install_reqs,
    packages=['bullock'],
)
