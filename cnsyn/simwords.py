# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 17:03:45 2021

@author: shangfr
"""
import joblib
import operator
from functools import reduce
from whoosh.index import open_dir
from whoosh.qparser import QueryParser
import pkg_resources

INDEX_DIR = pkg_resources.resource_filename('cnsyn', 'query')
ix = open_dir(INDEX_DIR)


words_tree = joblib.load(INDEX_DIR+'/words_tree_mini.m')

tree_model = words_tree['model']
words_id = words_tree['words']
words_emb = tree_model.get_arrays()[0]


def search(word, topK=10, origin='all'):
    '''
    Parameters
    ----------
    word : str
        查询词.
    topK : int, optional
        查询返回同义词数量. The default is 10.
    origin : str, optional
        词源. The default is 'all'.

    Returns
    -------
    sim_words : list
        同义词列表.

    '''

    word_list = []
    with ix.searcher() as searcher:
        query = QueryParser("words", ix.schema).parse(word)
        results = searcher.search(query, limit=None)

        if len(results) > 0:
            for result in results:
                if origin == 'all':
                    word_list.append(result.fields()['words'].split())
                elif origin == result.fields()['origin']:
                    word_list.append(result.fields()['words'].split())
                else:
                    pass
        if word_list != []:
            sim_words = reduce(operator.add, word_list)
            sim_words = list(set(sim_words))
        else:
            sim_words = word_list

    return sim_words[0:topK]


def anns(word, topK=10):

    '''
    Parameters
    ----------
    word : str
        查询词.
    topK : int, optional
        k nearest neighbors. The default is 10.
    return_distance : bool, optional
        if True, return distances to neighbors of each point if False, return only neighbors. The default is True.

    Returns
    -------
    sim_words : list
        同义词列表.

    '''

    word_key = [x[0] for x in words_id.items() if word == x[1]]

    if word_key == []:
        sim_words = []
    else:
        word_emb = words_emb[word_key]
        ind = tree_model.query(
            word_emb, k=topK, return_distance=False)
        sim_words = [words_id.get(i) for i in ind.ravel()]

    return sim_words


if __name__ == '__main__':

    # 查询同义词（全部词库）
    word = '中山广场'
    search(word)
    search(word, topK=3)
    # 使用wiki词库
    search(word, origin='wiki')
    # 使用中文同义词字典库
    search(word, origin='cndict')

    # 基于向量查同义词
    anns(word)
    anns(word, topK=3)
    
    word = input("Please input the word you want to search: ")
    step_result = "Something went wrong......"
    try:
        step_result = search(word)
    finally:
        print(step_result)
