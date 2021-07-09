# -*- coding: utf-8 -*-
"""
Created on Thu Jul  8 10:10:17 2021

@author: shangfr
"""

import joblib
import numpy as np
from sklearn.neighbors import BallTree
from sklearn.decomposition import PCA



def build_model(file_path, modeldir="query"):
    words_id_emb = np.load(file_path, allow_pickle=True).item()
    
    words_emb = words_id_emb['emb']
    words_id = words_id_emb['id']
    
    pca = PCA(n_components=0.6)
    words_transformed = pca.fit_transform(words_emb)
    tree = BallTree(words_transformed)
    # 存为字典
    words_tree = {'model': tree, 'words': words_id}
    joblib.dump(words_tree, filename=modeldir+'/words_tree_mini.m')
    return "-----------索引树已经构建完成---------- "

build_model('chinese_dictionary/words_id_emb.npy', modeldir="query")

words_tree = joblib.load('query/words_tree_mini.m')
tree_model = words_tree['model']
words_id = words_tree['words']
words_emb =  tree_model.get_arrays()[0]

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
        dist, ind = tree_model.query(word_emb, k=topK,return_distance=True)
        sim_words = [words_id.get(i) for i in ind.ravel()]

    return sim_words


anns('垃圾')
