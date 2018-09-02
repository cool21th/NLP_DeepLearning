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
    

## Where to get the vectors:

GloVe: https://nlp.stanford.edu/projects/glove/

Direct link: http://nlp.stanford.edu/data/glove.6B.zip/

Word2vec https://code.google.com/archive/p/word2vec/

direct link: https://drive.google.com/file/d/0B7XkCwpI5KDYNlNUTTlSS21pQmM/edit?usp=sharing


## Text Classification

Data representation: bag of words

ex) "I like football"
    Feature = [vec("I") + vec("like") + vec("football")]/3
    
Classifier: 
   Naive Bayes,
   Logistic Regeression,
   Random Forest,
   Extra Trees,
   Etc...
   
 Data: https://www.cs.umb.edu/~smimarog/textmining/datasets/
 
 Under: Reuters-21578 R8

## RNN

 Embedding layer => Recurrent unit => Dense layer

 Embedding layer: just the word embedding matrix

 Recurrent unit: Simple unit, GRU, or LSTM

 Dense layer: maps recurrent unit's output to one of the output classes


## CBOW : Continuous bag of words

Context size could be considered 2(or 4)

In practice, context size is usually set from 5-10

The input weight is W(1) for all input words


#### Article spinning

A site with lots of information is useful for lots of people

Internet marketers may try to capitalize on this by stealing others' content

An obious solution is to take exsiting articles, and replace parts of it with new words that retain the same meaning



## Skip gram

Like the opposite of CBOW

Helpful to think of it in terms of bigram

"The quick brown fox jumps over the lazy dog"
      
      Bigram model: jumps -> over
      Skipgram : jumps -> brown, jumps -> fix, jumps -> the
      

## Negative sampling

Instead of doing multiclass cross-entropy,
just do binary cross-entropy on the negative samples

using np.random.choice

      Input word: jumps
      Target words: brown, fox, over, the
      Negative samples: apple, orange, boat, tokyo
      
      J = logp(brown | jumps) + logp(fox | jumps) + logp(over | jumps) + logp(the | jumps) +
          log[1-p(apple | jumps) + log[1-p(orange | jumps)  + log[1-p(boat | jumps) + log[1-p(tokyo | jumps)
          
