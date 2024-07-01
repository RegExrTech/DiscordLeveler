import sys
sys.path.insert(0, 'Utils')
import json_helper
from collections import defaultdict

SCORES = json_helper.get_db('database/scores.json')

GAME = 'Crossword'

d = defaultdict(lambda: [])
for user in SCORES[GAME]:
	for date, score in SCORES[GAME][user].items():
		d[user].append(score)

for user in d:
	l = [int(x) for x in d[user]]
	l.sort()
	mean = sum(l)/len(l)
	median = l[len(l)//2]
	mode = max(set(l), key=l.count)
	print("=== " + str(user) + " ===")
	print(mean)
	print(median)
	print(mode)
	print(l[0])
	print(l[-1])
