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

Suppose V = 10,000

Then W contains V x V = 10^8 numbers(100 million)

Suppose D = 100

Then W1 and W2 contain 10^2 * 10 ^4 = 10^6 numbers each, 2 million total
