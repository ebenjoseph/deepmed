#!/usr/bin/env python
from deepdive import *
import random
from collections import namedtuple

NumLabel = namedtuple('SpouseLabel', 'num_id, label, type')

@tsv_extractor
@returns(lambda
  num_id   = "text",
  label   = "int",
  rule_id = "text",
:[])
# heuristic rules for finding positive/negative examples of spouse relationship mentions
def supervise(
  num_id="text", num_begin="int", num_end="int", num_text="text",
  doc_id="text", sentence_index="int", sentence_text="text",
  tokens="text[]", lemmas="text[]", pos_tags="text[]", ner_tags="text[]",
  dep_types="text[]", dep_token_indexes="int[]",
):

# Constants
POSITIVE_WORDS = frozenset(["control", "blind", "double-blind", "statistically significant", "follow-up", "longevity", "clinical significance", "confidence interval", "randomized", "randomised"])
NEGATIVE_WORDS = frozenset(["observational"])
MAX_DIST = 10

# Common data objects
front_lemmas = lemmas[:num_begin]
tail_lemmas = lemmas[num_end:]
front_ner_tags = ner_tags[:num_begin]
tail_ner_tags = ner_tags[num_end:]
num = NumLabel(num_id=num_id, label=None, type=None)

# Rule: positive words in front
if len(POSITIVE_WORDS.intersection(front_lemmas)) > 0:
  yield num._replace(label=1, type='pos:positive_word_front')

# Rule: positive words in tail
if len(POSITIVE_WORDS.intersection(tail_lemmas)) > 0:
  yield num._replace(label=1, type='pos:positive_word_tail')

# Rule: negative words in front
if len(NEGATIVE_WORDS.intersection(front_lemmas)) > 0:
  yield num._replace(label=-1, type='neg:negative_word_front')

# Rule: negative words in tail
if len(NEGATIVE_WORDS.intersection(tail_lemmas)) > 0:
  yield num._replace(label=-1, type='neg:negative_word_tail')

'''
# Rule: Candidates that are too far apart
if len(intermediate_lemmas) > MAX_DIST:
    yield spouse._replace(label=-1, type='neg:far_apart')

# Rule: Candidates that have a third person in between
if 'PERSON' in intermediate_ner_tags:
    yield spouse._replace(label=-1, type='neg:third_person_between')

# Rule: Sentences that contain wife/husband in between
#         (<P1>)([ A-Za-z]+)(wife|husband)([ A-Za-z]+)(<P2>)
if len(MARRIED.intersection(intermediate_lemmas)) > 0:
    yield spouse._replace(label=1, type='pos:wife_husband_between')

# Rule: Sentences that contain and ... married
#         (<P1>)(and)?(<P2>)([ A-Za-z]+)(married)
if ("and" in intermediate_lemmas) and ("married" in tail_lemmas):
    yield spouse._replace(label=1, type='pos:married_after')

# Rule: Sentences that contain familial relations:
#         (<P1>)([ A-Za-z]+)(brother|stster|father|mother)([ A-Za-z]+)(<P2>)
if len(FAMILY.intersection(intermediate_lemmas)) > 0:
    yield spouse._replace(label=-1, type='neg:familial_between')
'''