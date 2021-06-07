# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 17:03:45 2021

@author: shangfr
"""
import operator
from functools import reduce
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
import pkg_resources

INDEX_DIR = pkg_resources.resource_filename('cnsyn', 'query')

def search(word, indexdir=INDEX_DIR):
    '''

    Parameters
    ----------
    word : str
        搜索词.
    indexdir : str, optional
        索引位置. The default is "query".

    Returns
    -------
    sim_words : list
        同义词列表.

    '''

    ix = open_dir(indexdir)
    word_list = []
    with ix.searcher() as searcher:
        query = QueryParser("words", ix.schema).parse(word)
        results = searcher.search(query, limit=None)
        print("-------搜索已经完成-------")
        if len(results) > 0:
            for result in results:
                # print(result.fields())
                word_list.append(result.fields()['words'].split())
            #sim_words_l = [synonyms['words'].split() for synonyms in word_list]
            sim_words = reduce(operator.add, word_list)
            sim_words = list(set(sim_words))
        else:
            sim_words = []

    return sim_words


if __name__ == '__main__':

    # search("垃圾")

    word = input("Please input the word you want to search: ")
    step_result = "Something went wrong......"
    try:
        step_result = search(word)
    finally:
        print(step_result)
