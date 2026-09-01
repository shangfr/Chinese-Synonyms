"""cnsyn — 中文同义词查询工具包（词法召回）。

零运行时依赖：基于内存倒排索引的精确查表，可选 rapidfuzz/pypinyin 增强。

用法::

    import cnsyn

    cnsyn.search("垃圾")                # 精确查询
    cnsyn.search("垃圾", topK=3)        # 限制数量
    cnsyn.search("高兴", origin="wiki") # 按词源过滤
    cnsyn.search("gaoxing", pinyin=True)  # 拼音查询
    cnsyn.add_synonyms(["垃圾", "渣滓"])  # 运行时添加自定义同义词组
    cnsyn.load_user_dict("my_dict.txt")   # 批量加载用户词典
"""
from ._search import add_synonyms, load_user_dict, search

__version__ = "2.0.0"
__all__ = ("search", "add_synonyms", "load_user_dict", "__version__")
