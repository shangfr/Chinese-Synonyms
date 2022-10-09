# Chinese-Synonyms
Chinese Synonyms 中文同义词查询工具包
Chinese Synonyms for Natural Language Processing and Understanding.

cnsyn
=====

"cnsyn"：Python 中文同义词查询工具组件

"cnsyn" : Python Query tools for Chinese Synonyms.

GitHub: https://github.com/shangfr/Chinese-Synonyms

特点
====

-  支持同义词查询
-  支持自定义词典 > 已删除
-  Apache License 2.0 授权协议

在线演示： 

安装说明
========

-  全自动安装：``pip install cnsyn``
-  半自动安装：先下载 https://pypi.python.org/pypi/cnsyn/ ，解压后运行 ``python setup.py install``
-  手动安装：将 cnsyn 目录放置于当前目录或者 site-packages 目录，通过 ``import cnsyn`` 来引用。


同义词库说明
========
- 1、wiki：通过维基百科构建的一个中文同义词库-AitSimwords.txt；
- 2、cndict：中文同义词字典-chinese_dictionary.txt；
- 3、words_id_emb: 基于[PaddleNLP](https://gitee.com/paddlepaddle/PaddleNLP) TokenEmbedding的预训练模型获取的词向量，合并wiki、cndict词库，共计129691个词； 

查询原理
========
- 基于词的传统召回
    基于倒排索引，当用户输入查询词后，根据该词到倒排索引中进行查找该词的同义词。
    
- 基于向量的语义召回
    基于KNN-BallTree算法，找出某一个词向量最相近的词集合；

代码示例
========
```python
# encoding=utf-8

import cnsyn

# 查询同义词（全部词库）
word = '垃圾'
cnsyn.search(word)
cnsyn.search(word,topK=3)
# 使用wiki词库
cnsyn.search(word, origin='wiki')
# 使用中文同义词字典库
cnsyn.search(word, origin='cndict')

# 基于向量的语义召回Approximate Nearest Neighbor Search 
cnsyn.anns(word)
cnsyn.anns(word,topK=3)

```