import os
from codecs import open
from setuptools import find_packages, setup


VERSION = '0.0.10'

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-rehive-extras',
    version=VERSION,
    packages=find_packages(),
    include_package_data=True,
    description='Extras for Django',
    long_description=README,
    long_description_content_type='text/markdown',
    url='https://github.com/rehive/django-rehive-extras',
    download_url='https://github.com/rehive/django-rehive-extras/archive/{}.zip'.format(VERSION),
    author='Rehive',
    author_email='info@rehive.com',
    license='MIT',
    install_requires=["Django>=2.0"],
    python_requires='>=3.4',
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
