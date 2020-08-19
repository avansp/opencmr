from setuptools import setup, find_packages

setup(
    name='open-cmr',
    author='Avan Suinesiaputra',
    author_email='avan.sp@gmail.com',
    version='0.1.0',
    license='LICENSE',
    description='Open source Cardiac MRI analysis',
    packages=find_packages(),
    long_description=open('README.md').read(),
)