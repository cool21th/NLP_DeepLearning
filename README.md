# NLP_DeepLearning

## Datasets

word2vec and Glove

https://dumps.wikimedia.org/

Download as many as you want/have time to process

Look for the files with "pages-articles" in the filename

convert from XML to TXT with:

### 1. Ruby
    https://github.com/yohasebe/wp2txt/
    Put these TXT files into large_files, adjacent to the class folder
    install:sudo gem install wp2xt
    Run: wp2txt -i <filename>
  
### 2. Python
    https://github.com/attardi/wikiextractor/
    Clone the repo, run WikiExtractor.py or install using " python setup.py install"
    python WikiExtractor.py -o <output_dir> <input_file>
    


### Installing Ruby

    Easier way: sudo apt install ruby
    RVM(Ruby Version Manager): sudo apt install curl dirmngr
    rvm install ruby-2.2.0
    rvm use 2.2.0
    gem install wp2txt

