
from __future__ import print_function, division
from builtins import range

import os
import string
import sys
import operator

from sklearn.metrics.pairwise import pairwise_distances

# import nltk
# nltk.download()
from nltk.corpus import brown

import numpy as np


def find_analogies(w1, w2, w3, We, word2idx, idx2word):
    V, D = We.shape

    king = We[word2idx[w1]]
    man = We[word2idx[w2]]
    woman = We[word2idx[w3]]
    v0 = king - man - woman

    for dist in ('euclidean', 'cosine'):
        distances = pairwise_distances(v0.reshape(1,D), We, metric=dist).reshape(V)

        idx = distances.argsort()[:4]
        best_idx = -1
        keep_out = [word2idx[w] for w in (w1, w2, w3)]
        for i in idx:
            if i not in keep_out:
                best_idx = i
                break
        best_word = idx2word[best_idx]

        print("closest match by", dist, "distance: ", best_word)
        print(w1, "-", w2, "=",best_word, "-", w3)


def remove_punctuation_2(s):
    return s.translate(None, string.punctuation)


def remove_punctuation_3(s):
    return s.translate(str.maketrans('', '',string.punctuation))


if sys.version.startswith('2'):
    remove_punctuation = remove_punctuation_2
else:
    remove_punctuation = remove_punctuation_3


def my_tokenizer(s):
    s = remove_punctuation(s)
    s = s.lower()
    return s.split()


def get_wikipedia_data(n_files, n_vocab, by_paragraph=False):
    prefix = '../large_files/enwiki-articles1/AB/'
    print('prefix', os.path.exists(prefix))

    if not os.path.exists(prefix):
        print("Please download the data from https://dumps.wikimedia.org/")
        exit()

    print('os.listdir(prefix)', os.listdir(prefix))
    # input_files = [f for f in os.listdir(prefix) if f.startswith('wiki') and f.endswith('txt')]
    input_files = [f for f in os.listdir(prefix) if f.startswith('wiki')]

    print('input_files',input_files)

    if len(input_files) == 0:
        print("Please download the data from https://dumps.wikimedia.org/")
        exit()

    # return variables

    sentences = []
    word2idx = {'START' : 0, 'END': 1}
    idx2word = ['START', 'END']
    current_idx = 2
    word_idx_count = {0: float('inf'), 1: float('inf')}

    if n_files is not None:
        input_files = input_files[:n_files]

    for f in input_files:
        print("reading", f)
        for line in open(prefix + f, encoding='utf-8'):
            line = line.strip()

            if line and line[0] not in ('[', '*', '-', '|', '=', '{', '}'):
                if by_paragraph:
                    sentence_lines = [line]
                else:
                    sentence_lines = line.split('. ')
                for sentence in sentence_lines:
                    tokens = my_tokenizer(sentence)
                    for t in tokens:
                        if t not in word2idx:
                            word2idx[t] = current_idx
                            idx2word.append(t)
                            current_idx += 1
                        idx = word2idx[t]
                        word_idx_count[idx] = word_idx_count.get(idx,0) + 1

                    sentence_by_idx = [word2idx[t] for t in tokens]
                    sentences.append(sentence_by_idx)

    sorted_word_idx_count = sorted(word_idx_count.items(), key=operator.itemgetter(1), reverse=True)
    word2idx_small = {}

    new_idx = 0

    idx_new_idx_map ={}
    for idx, count in sorted_word_idx_count[:n_vocab]:
        word = idx2word[idx]
        print(word, count)
        word2idx_small[word] = new_idx
        idx_new_idx_map[idx] = new_idx
        new_idx += 1

    word2idx_small['UNKOWN'] = new_idx
    unknown = new_idx

    assert('START' in word2idx_small)
    assert('END' in word2idx_small)
    assert('king' in word2idx_small)
    assert('queen' in word2idx_small)
    assert('man' in word2idx_small)
    assert('woman' in word2idx_small)

    sentence_small = []
    for sentence in sentences:
        if len(sentence) > 1:
            new_sentence = [idx_new_idx_map[idx] if idx in idx_new_idx_map else unknown for idx in sentence]
            sentence_small.append(new_sentence)

    return sentence_small, word2idx_small

KEEP_WORDS = set([
    'king', 'man', 'queen', 'woman',
    'italy', 'rome', 'france', 'paris',
    'london', 'britain', 'england',
])

def get_sentences():
    # returns 57340 of the Brown corpus
    # each sentence is represented as a list of individual string tokens
    return brown.sents()


def get_sentences_with_word2idx():
    sentences = get_sentences()
    indexed_sentences = []

    i = 2
    word2idx = {'START': 0, 'END': 1}
    for sentence in sentences:
        indexed_sentence = []
        for token in sentence:
            token = token.lower()
            if token not in word2idx:
                word2idx[token] = i
                i +=1
            indexed_sentence.append(word2idx[token])
        indexed_sentences.append(indexed_sentence)
    print("Vocab size: ", i)
    return indexed_sentences, word2idx

def get_sentences_with_word2idx_limit_vocab(n_vocab=2000, keep_words=KEEP_WORDS):
    sentences = get_sentences()
    indexed_sentences = []

    i = 2
    word2idx = {'START': 0, 'END': 1}
    idx2word = ['START', 'END']

    word_idx_count = {
        0: float('inf'),
        1: float('inf')
    }

    for sentence in sentences:
        indexed_sentence = []
        for token in sentence:
            token = token.lower()
            if token not in word2idx:
                idx2word.append(token)
                word2idx[token] = i
                i += 1

            idx = word2idx[token]
            word_idx_count[idx] = word_idx_count.get(idx, 0) +1

            indexed_sentence.append(idx)
        indexed_sentences.append(indexed_sentence)

    # restrict vocab size
    for word in keep_words:
        word_idx_count[word2idx[word]] = float('inf')

    sorted_word_idx_count = sorted(word_idx_count.items(), key=operator.itemgetter(1), reverse=True)
    word2idx_small = {}
    new_idx = 0

    idx_new_idx_map = {}
    for idx, count in sorted_word_idx_count[:n_vocab]:
        word = idx2word[idx]
        print(word, count)
        word2idx_small[word] = new_idx
        idx_new_idx_map[idx] = new_idx
        new_idx += 1

    word2idx_small['UNKOWN'] = new_idx
    unknown = new_idx

    assert('START' in word2idx_small)
    assert('END' in word2idx_small)
    for word in keep_words:
        assert(word in word2idx_small)

    sentence_small = []
    for sentence in indexed_sentences:
        if len(sentence) > 1:
            new_sentence = [idx_new_idx_map[idx] if idx in idx_new_idx_map else unknown for idx in sentence]
            sentence_small.append(new_sentence)
    return sentence_small, word2idx_small


def init_weight(Mi, Mo):
    return np.random.randn(Mi, Mo) / np.sqrt(Mi + Mo)


