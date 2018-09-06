
## Natural Language Processing

[A dive into Natural Language Processing](https://medium.com/greyatom/a-dive-into-natural-language-processing-103ae0b0a588)

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

      # Porter Stemmer
      from nltk.stem.porter import PorterStemmer
      porter_stemmer = PorterStemmer()
      porter_stmeer.stem("crying")
      
      >> 'cri'
            
      from nltk.stemlancaster import LancasterStemmer
      lancaster_stemmer = LancasterStemmer()
      

## Bag of word in NLP

[An Introduction to Bag-of-words in NLP](https://medium.com/greayatom/an-introduction-to-bag-of-words-in-nlp-ac967d43b428/)

