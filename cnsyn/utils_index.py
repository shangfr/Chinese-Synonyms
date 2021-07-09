# -*- coding: utf-8 -*-
"""
Created on Thu Jun  3 17:03:45 2021

@author: shangfr
"""
import joblib
import numpy as np
from sklearn.neighbors import BallTree
import os
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD

# 创建schema, stored为True表示该字段内容能够在检索结果中显示


def build_index(file_path, indexdir="indexdir"):
    schema = Schema(title=TEXT(stored=True), origin=ID(
        stored=True), words=KEYWORD(stored=True))
    if not os.path.exists(indexdir):
        os.mkdir(indexdir)
    ix = create_in(indexdir, schema)
    writer = ix.writer()
    with open(file_path, 'r', encoding='utf-8') as filereader:
        num = 1
        for row in filereader:
            title_num = str(num) + " line"
            origin = 'cndict' if num > 28043 else 'wiki'
            writer.add_document(title=title_num, origin=origin, words=row)
            num += 1
    writer.commit()
    return "-----------索引已经构建完成---------- "

def build_model(file_path, modeldir="query"):
    words_id_emb = np.load(file_path, allow_pickle=True).item()
    
    words_emb = words_id_emb['emb']
    words_id = words_id_emb['id']
    tree = BallTree(words_emb)
    # 存为字典
    words_tree = {'model': tree, 'words': words_id}
    joblib.dump(words_tree, filename=modeldir+'/words_tree.m')
    return "-----------索引树已经构建完成---------- "

if __name__ == '__main__':

    build_index('chinese_dictionary/sim_words.txt', indexdir="query")
    build_model('chinese_dictionary/words_id_emb.npy', modeldir="query")