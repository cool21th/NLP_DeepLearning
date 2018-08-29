# NLP_DeepLearning

## Datasets

## Wiki datasets

https://dumps.wikimedia.org/

Download as many as you want/have time to process

    2018-00-00 15:32:20 enwiki: Dump complete
    enwiki-20180000-pages-articles1.xml-p10p30302.bz2 1XX.0 MB

Look for the files with "pages-articles" in the filename

convert from XML to TXT with:

#### 1. Ruby
    https://github.com/yohasebe/wp2txt/
    Put these TXT files into large_files, adjacent to the class folder
    install:sudo gem install wp2xt
    Run: wp2txt -i <filename>
  
#### 2. Python
    https://github.com/attardi/wikiextractor/
    Clone the repo, run WikiExtractor.py or install using " python setup.py install"
    python WikiExtractor.py -o <output_dir> <input_file>
    


#### Installing Ruby

    Easier way: sudo apt install ruby
    RVM(Ruby Version Manager): sudo apt install curl dirmngr
    rvm install ruby-2.2.0
    rvm use 2.2.0
    gem install wp2txt

## Pos tagging

http://www.cnts.ua.ac.be/conll2000/chunking/

## NER

https://github.com/artter/twitter_nlp/blob/master/data/annotated/ner.txt

## Sentiment analysis

http://nlp.stanford.edu/sentiment/
