# wa-analytics-light

Acknowledgement : Thiago Salles [tsalles@br.ibm.com] is the original author. It's just an excerpt with minor debugging.

# Dependencies
```
watson_developer_cloud
```

# Run k-fold test 
Move to the root of the project. Then:
```
python kfold_cv.py \
  -w 12345678-abcd-1234-1234-1234567abcde \ # --workspace_id
  -u 87654321-zxcv-5678-qwer-asdfghja1234 \ # --username
  -p 12345abcde12 \ # --password
  -i ./dir_to_hold_experiment_data \ # --folds-dir, Directory containing folds to be re-used by the experiments
  -l ko \ # --language, Language code to train the system under another language configuration
  -k 10 \ # --num-folds, Number of cross validation folds
  -f ./results_20180605 # --results-folder, Directory for storing test results and temporary files
```
For example,
```
python kfold_cv.py \
  -w 12345678-abcd-1234-1234-1234567abcde \
  -u 87654321-zxcv-5678-qwer-asdfghja1234 \
  -p 12345abcde12 \
  -i ./dir_to_hold_experiment_data \
  -l ko \
  -k 10 \
  -f ./results_20180605
```
Please confer the buttommost lines of `kfold_cv.py` if things are not clear.

# How to generate report
```
python analyze_experiment.py -i ./dir-which-holds-result
```
For example, if you have run the testing example above, it should be somthing like:

```
python analyze_experiment.py -i ./results_20180605
```
After running it, you will find a html file generated in the directory you have put as argument.
