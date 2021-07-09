# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 15:58:15 2021

@author: shangfr
"""


from functools import partial
import argparse
import os

import numpy as np
import paddle

import paddlenlp as ppnlp
from paddlenlp.data import Tuple, Pad
from paddlenlp.datasets import MapDataset
from paddlenlp.utils.log import logger

from base_model import SemanticIndexBase
from data import convert_example, create_dataloader
from data import gen_id2corpus


parser = argparse.ArgumentParser()
parser.add_argument("--corpus_file", type=str,
                    default="words.txt", help="The full path of input file")
parser.add_argument('--device', choices=['cpu', 'gpu'], default="cpu",
                    help="Select which device to train model, defaults to gpu.")
parser.add_argument("--max_seq_length", default=64, type=int, help="The maximum total input sequence length after tokenization. "
                    "Sequences longer than this will be truncated, sequences shorter will be padded.")
parser.add_argument("--output_emb_size", default=256,
                    type=int, help="output_embedding_size")
parser.add_argument("--params_path", type=str, default="batch_neg_v1.0\model_state.pdparams",
                    help="The path to model parameters to be loaded.")
parser.add_argument("--batch_size", default=512, type=int,
                    help="Batch size per GPU/CPU for training.")
args = parser.parse_args()

'''
aList = []
with open("chinese_dictionary/sim_words.txt", "r",encoding='utf-8') as f:
    for line in f.readlines():
        res = list(filter(None,line.strip('\n').split(" ")))
        aList.extend(res)

words = list(set(aList))


with open("words.txt", 'w',encoding='utf-8') as f:
    for i in words:
        f.write(i + '\n')

'''


if __name__ == "__main__":

    paddle.set_device(args.device)
    rank = paddle.distributed.get_rank()
    if paddle.distributed.get_world_size() > 1:
        paddle.distributed.init_parallel_env()

    tokenizer = ppnlp.transformers.ErnieTokenizer.from_pretrained('ernie-1.0')

    trans_func = partial(
        convert_example,
        tokenizer=tokenizer,
        max_seq_length=args.max_seq_length)

    batchify_fn = lambda samples, fn=Tuple(
        Pad(axis=0, pad_val=tokenizer.pad_token_id),  # text_input
        Pad(axis=0, pad_val=tokenizer.pad_token_type_id),  # text_segment
    ): [data for data in fn(samples)]

    pretrained_model = ppnlp.transformers.ErnieModel.from_pretrained(
        "ernie-1.0")

    model = SemanticIndexBase(
        pretrained_model, output_emb_size=args.output_emb_size)
    model = paddle.DataParallel(model)

    # Load pretrained semantic model
    if args.params_path and os.path.isfile(args.params_path):
        state_dict = paddle.load(args.params_path)
        model.set_dict(state_dict)
        logger.info("Loaded parameters from %s" % args.params_path)
    else:
        raise ValueError(
            "Please set --params_path with correct pretrained model file")

    # Need better way to get inner model of DataParallel
    inner_model = model._layers

    # text2emb
    id2corpus = gen_id2corpus(args.corpus_file)
    # np.save('id2word.npy',id2corpus)
    #x12 = np.load('id2word.npy',allow_pickle=True)
    #x123 = x12.item()
    # conver_example function's input must be dict
    corpus_list = [{idx: text} for idx, text in id2corpus.items()]
    corpus_ds = MapDataset(corpus_list)

    corpus_data_loader = create_dataloader(
        corpus_ds,
        mode='predict',
        batch_size=args.batch_size,
        batchify_fn=batchify_fn,
        trans_fn=trans_func)

    from tqdm import tqdm
    with tqdm(total=len(id2corpus)//args.batch_size) as pbar:
        pbar.set_description('Embedding Processing:')
        all_embeddings = []
        for text_embeddings in inner_model.get_semantic_embedding(corpus_data_loader):
            all_embeddings.append(text_embeddings.numpy())
            pbar.update(1)

    all_embeddings = np.concatenate(all_embeddings, axis=0)

    # np.save('words_embeddings',all_embeddings)

    words_id_emb = {'emb': all_embeddings, 'id': id2corpus}
    np.save('words_id_emb', words_id_emb)
