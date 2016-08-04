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

Select `cmudict` and `punkt`.

### Configure AWS

```shell
$ aws configure
```

Enter your AWS credentials, and use the default of `None` for the region.

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

## Working with Data

Data is stored in AWS S3, specifically the `s3://deepmed-data` bucket. The data
are fetched into the not version controlled `data/raw` folder so you can work with
it locally.

To push a new data file (note that independent of the path the file will be placed
directly into the `deepmed-data` bucket):

```shell
$ ./bin/s3push /path/to/data/file.jsonl
```

To fetch that file into the local `data/raw/` folder run:

```shell
# make data/raw/file.jsonl
```

With raw data in hand, you're ready to transform it. Try keeping the derivative
data under `data/build` and add new make targets to the `Makefile` to automate
building the data.
