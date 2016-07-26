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
