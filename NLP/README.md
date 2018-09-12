
## Natural Language Processing

Reference: [A dive into Natural Language Processing](https://medium.com/greyatom/a-dive-into-natural-language-processing-103ae0b0a588)

* Wikipedia: Natural-Language Processing is an area of computer science and artificial intelligence 
concerned with the interactions between computers and human(natural) languages, in partifular hot to 
program computers to fruifully process large amounts of natrual language data.

-> NLP is the ability of computers to understand human speech as it is spoken. NLP helps to analyze,
understand, and derive meaning from human language in a smart and useful way

* NLP Algoritms are machine learning algorithms based.
* Output : Automatic summarization, Machine translation, Named entity recognition, Relationship extraction,
Sentiment analysis, Speech recognition, Topic Segment etc.

-----------------
* start using nltk
    
      import nltk
      text = open("text_data.txt").read()

* Sentence Segmentaion
      
      sents = nltk.sent_tokenize(text)
    
* Tokenizaation

      from nltk.tokenize import RegexpTokenizer
      tokenizer = RegexpTokenizer(r'\w+')
      tokenizer.tokenize(sents[0])

* Stop words
      
      from nltk.corpus import stopwords
      stop_words = set(stopwords.words('english'))
      
      filtered_sentence = []
      for word in tokens:
        if word not in stop_words:
          filtered_sentence.append(word)

* Stemming and Lemmatization
      
      ##### Stemming #####
      # Porter Stemmer
      from nltk.stem.porter import PorterStemmer
      porter_stemmer = PorterStemmer()
      porter_stmeer.stem("crying")
      
      >> 'cri'
      
      # Lancaster Stemmer
      from nltk.stemlancaster import LancasterStemmer
      lancaster_stemmer = LancasterStemmer()
      lancaster_stemmer.stem("crying")
      
      >> 'cry'
      
      # Snowball Stemmer
      from nltk.stem import SnowballStemmer
      snowball_stemmer = SnowballStemmer("english)
      snowball_stemmer.stem("crying")
      
      >> 'cri'
      
      #### Lemmatization ####
      
      from nltk.stem import WordNetLemmatizer
      wordnet_lemmatizer = WordNetLemmatizer()
      wordnet_lemmatizer.lemmatize("came", pos="v")
      
      >> 'come'
      

## Bag of word in NLP

Reference: [An Introduction to Bag-of-words in NLP](https://medium.com/greayatom/an-introduction-to-bag-of-words-in-nlp-ac967d43b428/)

* Bag-of-Words: tokenized words(gram) for each observation and find out the frequency of each token

* The process of converting NLP text into numbers is called vectorization in Machine Learning
1. Counting the number of times each word appears in a document
2. Calculating the frequency that each word apeears in a document out of all the words in the document


* CountVectorizer
        
        from sklearn.feature_extraction.text import CountVectorizer, TfidVectorizer
        vect = CountVectorizer()
        
        from nltk.tokenize import TreebankwordTokenizer
        tokenizer = TreebankWordTokenizer()
        vect.set_params(tokenizer=tokenizer.tokenize)
        
        vect.set_params(stop_words='english')
        
        # 1-grams -> 2-grams
        vect.set_params(ngram_range(1,2))
        
        # ignore terms more than 50% of the documents
        vect.set_params(max_df=0.5)
        
        # least 2 documents
        vect.set_params(min_df=2)
        

* TF-IDF Vectorizer

        from sklearn.feature_extraction.text import TfidVectorizer
        vect = TfidVectorizer()

        from nltk.tokenize import TreebankWordTokenizer
        tokenizer = TreebackWordTokenizer()
        vect.set_params(tokenizer=tokenizer.tokenize)
        
        vect.set_params(stop_words='english')
        vect.set_params(ngram_range(1,2))
        
        vect.set_params(max_def=0.5)
        
        vect.set_params(min_df=2)


## Bag of Words model issues
1. Fixed-sized input
2. Doesn't take word order into account
3. Fixed-sized output

-> Answer is RNNs

-----------------------------

## Parts-of-Speech Tagging for Neural Network

        Logistic regression : p(tag|word) = softmax(W[word_index])
            -> only maps word to tag
            -> one word can have multiple tags
        RNNs :
            -> Sometimes LSTM beats GRU, sometimes the opposite
        HMMs


#### Hidden Markov Models

Hidden states = POS tags, observed = words

HMM = pi, A, B

pi = frequency of start tags

A = p(tag(t) | tag(t-1))

B = p(word(t) | tag(t))

All can be calculated by just counting


------------------------------

## Named Entity Recognition

        Logistic regression
        Recurrent neural network

simiar to POS taggin 

Named entites: person, company, location, etc


        


