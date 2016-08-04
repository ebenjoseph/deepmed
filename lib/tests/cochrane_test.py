# -*- coding: utf-8 -*-
import unittest

from .. import cochrane


class CochraneTest(unittest.TestCase):
    def setUp(self):
        self.COCHRANE_REVIEW_1 = {
            'ReviewURL': 'http://onlinelibrary.wiley.com/doi/10.1002/14651858.CD002898.pub5/full',
            'pubmedurl': 'http://www.ncbi.nlm.nih.gov/pubmed/4909228',
            'citation': 'Graupner K, Klein S, Müller F. Treatment of dendritic keratitis [Die Behandlung der Keratitis dendritica]. Advances in Ophthalmology 1969;21:113‐31.',
            'table': {
                'Random sequence generation (selection bias)': [
                    'Low risk',
                    'The investigators describe a random component in the sequence generation process'
                ],
                'Allocation concealment (selection bias)': [
                    'Unclear risk',
                    'Insufficient information'
                ],
                'Blinding (performance bias and detection bias)   All outcomes': [
                    'High risk',
                    'Lack of masking could have influenced outcome assessment'
                ],
                'Incomplete outcome data (attrition bias)   All outcomes': [
                    'High risk',
                    'Incomplete primary outcome data (outcome day unclear)'
                ],
                'Selective reporting (reporting bias)': [
                    'Unclear risk',
                    'Insufficient information'
                ],
                'Other bias': [
                    'Unclear risk',
                    'Insufficient information'
                ]
            }
        }

        self.COCHRANE_REVIEW_2 = {
            'ReviewURL': 'http://onlinelibrary.wiley.com/doi/10.1002/14651858.CD000006.pub2/full',
            'pubmedurl': 'http://www.ncbi.nlm.nih.gov/pubmed/4617592',
            'citation': 'Beard RJ, Boyd I, Sims CD. A trial of polyglycolic acid and chromic catgut sutures in episiotomy repair. British Journal of Clinical Practice 1974;28:409‐10.',
            'table': {
                'Adequate sequence generation?': [
                    'Low risk',
                    'Random number generator.'
                ],
                'Allocation concealment?': [
                    'Low risk',
                    'Sealed, numbered opaque envelopes.'
                ],
                'Blinding?   Women': [
                    'Low risk',
                    'Described as \'blinded\'.'
                ],
                'Blinding?   Clinical staff': [
                    'High risk',
                    'Not feasible. Different suture materials.'
                ],
                'Blinding?   Outcome assessors': [
                    'High risk',
                    'Not feasible. Different suture materials.'
                ],
                'Incomplete outcome data addressed?   All outcomes': [
                    'Unclear risk',
                    'Day 1 follow up 89%, day 3 96%, 81% at 6 months. Missing data for some outcomes.'
                ],
                'Free of other bias?': [
                    'Unclear risk',
                    'Some baseline imbalance (e.g. there were more primiparous women in the synthetic suture group (54.6%) vs 40% in the catgut group; the authors carried out further analysis to adjust for this).'
                ]
            }
        }


    def normalize_test(self):
        self.assertEqual({
            'allocation concealment': 0,
            'blinding': -1,
            'incomplete outcome data': -1,
            'sequence generation': 1,
            'selective reporting': 0,
        }, cochrane.normalize(self.COCHRANE_REVIEW_1))
        self.assertEqual({
            'allocation concealment': 1,
            'blinding': cochrane.MULTIPLE,
            'incomplete outcome data': 0,
            'sequence generation': 1,
            'selective reporting': cochrane.NA,
        }, cochrane.normalize(self.COCHRANE_REVIEW_2))
