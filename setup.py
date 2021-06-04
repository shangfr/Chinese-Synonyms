# -*- coding: utf-8 -*-
from distutils.core import setup
LONGDOC = """
Cnsyn
=====

"Cnsyn"：Python 中文同义词查询工具组件

"Cnsyn" : Python Query tools for Chinese Synonyms.

完整文档见 ``README.md``

GitHub: https://github.com/shangfr/Chinese-Synonyms

特点
====

-  支持同义词查询
-  支持自定义词典
-  Apache License 2.0 授权协议

在线演示： 

安装说明
========

-  全自动安装： ``easy_install Cnsyn`` 或者  ``pip install Cnsyn``
-  半自动安装：先下载 https://pypi.python.org/pypi/Cnsyn/ ，解压后运行
   python setup.py install
-  手动安装：将 Cnsyn 目录放置于当前目录或者 site-packages 目录
-  通过 ``import Cnsyn`` 来引用

"""

setup(name='cnsyn',
      version='0.0.1',
      description='Query tools for Chinese Synonyms',
      long_description=LONGDOC,
      author='ShangFR',
      author_email='shangfr@foxmail.com',
      url='https://github.com/shangfr/Chinese-Synonyms',
      license="Apache License 2.0",
      classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License 2.0',
        'Operating System :: OS Independent',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: Chinese (Traditional)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Word Processing',
        'Topic :: Word Processing :: Indexing',
        'Topic :: Word Processing :: Linguistic',
      ],
      keywords='NLP,tokenizing,Chinese Synonyms',
      packages=['cnsyn'],
      package_dir={'cnsyn':'cnsyn'},
      package_data={'cnsyn':['*.*','query/*']}
)
