# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 17:03:45 2021

@author: shangfr
"""
import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(name='cnsyn',
                 version='1.0.0',
                 description='Query tools for Chinese Synonyms',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 author='ShangFR',
                 author_email='shangfr@foxmail.com',
                 url='https://github.com/shangfr/Chinese-Synonyms',
                 classifiers=[
                     "Programming Language :: Python :: 3",
                     "License :: OSI Approved :: Apache Software License",
                     "Operating System :: OS Independent",
                 ],
                 keywords='NLP,simwords,Chinese Synonyms',
                 packages=setuptools.find_packages(),
                 # install_requires=['whoosh'],  # Optional
                 package_data={'cnsyn': ['*.*', 'query/*', 'chinese_dictionary/*']}
                 )

# python setup.py sdist bdist_wheel
# twine upload --repository pypitest dist/*
# twine upload dist/*