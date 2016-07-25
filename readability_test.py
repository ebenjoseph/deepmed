#!/usr/bin/env python
import json
from lib import readability

contentWords = ['Abstract', 'Method', 'Summary', 'Result', 'Conclusion', 'Discussion', 'Material', 'Future']

if __name__ == '__main__':
    with open('Arduino_ES_output_filtered.jsonl') as f:
        for line in f:
            data = json.loads(line)

            contentString = ""

            # content extractor
            for key in data['content']:
                for word in contentWords:
                    #print key, word
                    if key.lower().find(word.lower()) >= 0:
                        #print data['content'][key]
                        contentString += data['content'][key]
                        contentString += ' '

            print readability.extract(contentString)
