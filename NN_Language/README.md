## Language model

Language model: a model of the probability of a sequence of words

Bigram : 2 consecutive words in a sentence

N-grams : a sequence of N consecutive words

Bayes Rule : p(A -> B -> C) = p(C|A -> B)p(A -> B) = p(C|A -> B)p(B|A)p(A)

      p(A) = count(A) / corpus length
      p(C| A, B) = count(A-> B-> C) / count(A-> B)

Markov Assumption : depends only on what I saw int the previous step

      p(E|A, B, C, D) = p(E|D)
      

## Neural Network Bigram Model

old(Logistic Regression): p(y | x) = softmax(W^T * X)
new(Neural Network): p(y | x) = softmax(W2^T * h)  (h = tanh(W1^T * x)


## Hyperparameters

Always something you need to think about in deep learning / neural networks

What should the hidden layer size == "D"

Then: shape(W1) == V x D

      shape(W2) == D X V

V is vocabulary size, D is an arbitrary hyper parameter

D << V (D is much smaller than V)

-> Autoencode pattern : Bottleneck(Compress V dimensions into D dimensions)

## Logistic Regression for Language Model

Recall: it was very slow

      Elapsed time training:  0:43:18.612436
      avg_bigram_loss:  3.98941154221291

Suppose V = 10,000

Then W contains V x V = 10^8 numbers(100 million)

Suppose D = 100

Then W1 and W2 contain 10^2 * 10 ^4 = 10^6 numbers each, 2 million total

ex) Neural Network Model

      Elapsed time training: 0:08:09.506799
      avg_bigram_loss: 3.7779453269292613
