# deepmed

## Install

### Python Deps

Install the python dependences, preferably in a
[virtualenv](https://pypi.python.org/pypi/virtualenvwrapper):

```shell
$ pip install -r requirements.txt
```

### Readability NLTK Data

Install the CMU corpus and Punkt tokenizer models:

```python
>>> import nltk
>>> nltk.download()
```

Select `corpora/cmudict` and `models/punkt`.

## Full Pipeline

Assuming you are starting with the output of a parsed library jsonl file (e.g., Elsevier):

1. Move file into BigGuns: ~/nlp/raw_inputs
2. Extract relevant sections (e.g., for pval: abstract, summary, methods). Set outfile to be in ~/nlp/modeling and name accordingly
3. Run nlp markup script located in ~/nlp, output to ~/nlp/models
4. Import the new article and section tables into DD
5. Run relevant shell scripts (make sure models still look good)
6. Extract information via queries
7. Move csv extraction files into ~/modeling/csv_outputs
8. Run full extractor script in ~/modeling
9. Done with pipeline, now go to data science :)

