# Chinese-Synonyms
Chinese Synonyms 中文同义词查询工具包

cnsyn
=====

"cnsyn"：Python 中文同义词查询工具组件

"cnsyn" : Python Query tools for Chinese Synonyms.

GitHub: https://github.com/shangfr/Chinese-Synonyms

特点
====

-  支持同义词查询
-  支持自定义词典
-  Apache License 2.0 授权协议

在线演示： 

安装说明
========

-  全自动安装： ``easy_install cnsyn`` 或者  ``pip install cnsyn``
-  半自动安装：先下载 https://pypi.python.org/pypi/cnsyn/ ，解压后运行
   python setup.py install
-  手动安装：将 cnsyn 目录放置于当前目录或者 site-packages 目录
-  通过 ``import cnsyn`` 来引用

代码示例
========
```python
# encoding=utf-8

import cnsyn

cnsyn.search('垃圾')
```
输出:
-------搜索已经完成-------
Out[2]: 
        ['废料',
         '废品',
         '污染源',
         '滓',
         '渣滓',
         '渣',
         '排泄物',
         '杂质',
         '污物',
         '破烂',
         '废弃物',
         '垃圾堆',
         '破铜烂铁',
         '垃圾',
         '废物',
         '下脚']