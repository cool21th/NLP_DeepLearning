## TF-IDF : Term Frequency-Inverse Document Frequncy

Words that appear in many documents are probably less meaningful

Intuitively, our "modified count" becomes: Raw word count/ Document count

## Word Embedding

Word embedding is the collective name for a set of language modeling and feature learning techniques in natural language processing (NLP) where words or phrases from the vocabulary are mapped to vectors of real numbers.(from Wikipedia)

-> A categorical entity(a word) into a vector space

## Word Analogy

A word analogy compares the relationship between two pairs of words. 

   ex) King - Queen ~= Prince - Princess
       France - Paris ~= Germany - Berlin
       Brother - Sister ~= Uncle - Aunt


How to find analogies 

    There are 4 words in every analogy
    Input: 3 words
    Output: find the 4th word
    
    ex) King - Man = ? - Woman
        King - Man + Woman = ? (unkown vector)
        
    Key point = Use vector distnace to find the closest matching word
    
    closest_distance = infinity
    best_word = None
    test_vector = king - man + woman
    for word, vector in vocabulary:
        distance = get_distance(test_vector, vector)
        if distance < closest_distance:
            closest_distance = distance
            best_word = word
            

## Dimensionality

Doing TF-IDF and couting across many words and documents, we can not see dimensions

t-SNE can help us reduce dimensionality
    t-SNE: t-Distributed Sotchastic Neighbor Embedding(https://lvdmaaten.github.io/tsne/)
    

## WHERE TO GET THE VECTORS:
      GloVe: https://nlp.stanford.edu/projects/glove/
      Direct link: http://nlp.stanford.edu/data/glove.6B.zip

