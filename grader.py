import sys
sys.path.insert(0, 'Utils')
import requests
import re
import json
from collections import defaultdict
import datetime

import json_helper
import constants
import discord_helper

SCORES = json_helper.get_db('database/scores.json')
COMPLETED_GAMES = json_helper.get_db('database/completed_games.json')
COMPLETED_DAYS = json_helper.get_db('database/completed_days.json')

WORDLE = 'Wordle'
CONNECTIONS = 'Connections'
CROSSWORD = 'Crossword'
STRANDS = 'Strands'

WORDLE_START_DATE = '2021-06-19'
CONNECTIONS_START_DATE = '2023-06-11'
STRANDS_START_DATE = '2024-03-04'

DID_NOT_FINISH_SCORE = "DID NOT FINISH"

TOKENS = constants.TOKENS
homeworkURL = constants.baseURL.format(TOKENS["channels"]["homework"])

last_message_id = constants.last_message_id
most_recent_message_id = ""

connections_squares = ['🟦', '🟪', '🟩', '🟨']
strands_emojis = ['🔵', '🟡', '💡']
medals = ['🥇', '🥈', '🥉']

def count_medals(completed_games, scores):
	message_title = "Medal Counts"
	data = discord_helper.get_embedded_messaged_template(title=message_title)
	medal_counts = {}
	for game in completed_games.keys():
		medal_counts[game] = defaultdict(lambda: {0: 0, 1: 0, 2: 0})
		for game_number in completed_games[game]:
			temp_scores = defaultdict(lambda: [])
			for user in scores[game]:
				if scores[game][user][game_number] == DID_NOT_FINISH_SCORE:
					_score = 1
					_found_scores = [scores[game][player][game_number] for player in scores[game].keys() if isinstance(scores[game][player][game_number], int)]
					if _found_scores:
						_score += max(_found_scores)
				else:
					_score = scores[game][user][game_number]
				temp_scores[_score].append(user)
			score_list = list(temp_scores.keys())
			score_list.sort()
			users_accounted_for = 0
			for _score in score_list:
				for _id in temp_scores[_score]:
					medal_counts[game][_id][users_accounted_for] += 1
				users_accounted_for += len(temp_scores[_score])

	# Determine overall winner counts
	medal_counts['Daily Winner'] = defaultdict(lambda: {0: 0, 1: 0, 2: 0})
	derived_completions = defaultdict(lambda: 0)
	for game in completed_games:
		for game_date in completed_games[game]:
			if game == "Wordle":
				game_date = get_date_from_game_num(WORDLE_START_DATE, game_date)
			if game == "Connections":
				game_date = get_date_from_game_num(CONNECTIONS_START_DATE, game_date)
			if game == "Strands":
				game_date = get_date_from_game_num(STRANDS_START_DATE, game_data)
			derived_completions[game_date] += 1
	for date in derived_completions:
		if derived_completions[date] == len(list(completed_games.keys())):
			wordle_game_num = get_game_num_from_game_date(date, WORDLE_START_DATE)
			connections_game_num = get_game_num_from_game_date(date, CONNECTIONS_START_DATE)
			strands_game_num = get_game_num_from_game_date(date, STRANDS_START_DATE)
			# Get Rankings
			points = defaultdict(lambda: 0)
			for game in scores.keys():
				temp_scores = defaultdict(lambda: [])
				if game == 'Wordle':
					game_number = wordle_game_num
				elif game == 'Connections':
					game_number = connections_game_num
				elif game == "Strands":
					game_number = strands_game_num
				else:
					game_number = date
				for user in scores[game]:
					if scores[game][user][game_number] == DID_NOT_FINISH_SCORE:
						_score = 1
						_found_scores = [scores[game][x][game_number] for x in scores[game].keys() if isinstance(scores[game][x][game_number], int)]
						if _found_scores:
							_score += max(_found_scores)
					else:
						_score = scores[game][user][game_number]
					temp_scores[_score].append(user)
				score_list = list(temp_scores.keys())
				score_list.sort()
				users_accounted_for = 0
				for _score in score_list:
					game_points = len(list(scores[game].keys())) - users_accounted_for
					for id in temp_scores[_score]:
						points[id] += game_points
					users_accounted_for += len(temp_scores[_score])
			temp_scores = defaultdict(lambda: [])
			for id in points:
				temp_scores[points[id]].append(id)
			ranks = defaultdict(lambda: [])
			users_accounted_for = 0
			scores_list = list(temp_scores.keys())
			scores_list.sort()
			for score in scores_list[::-1]:
				ranks[users_accounted_for] += temp_scores[score]
				users_accounted_for += len(temp_scores[score])
			users_accounted_for = 0
			for _rank in ranks:
				for _id in ranks[_rank]:
					medal_counts['Daily Winner'][_id][users_accounted_for] += 1
				users_accounted_for += len(ranks[_rank])
	for game in medal_counts:
		data['embed']['fields'] = [{'name': game + " Medals", 'value': "", 'inline': False}] + data['embed']['fields']
		# Calculate order
		overall_scores = defaultdict(lambda: [])
		for user in medal_counts[game]:
			total_games = sum([medal_counts[game][user][x] for x in medal_counts[game][user]])
			overall_score = (medal_counts[game][user][0] * total_games * total_games) + (medal_counts[game][user][1] * total_games) + (medal_counts[game][user][0])
			overall_scores[overall_score].append(user)
		scores = list(overall_scores.keys())
		scores.sort()
		for score in scores[::-1]:
			for user in overall_scores[score]:
				data['embed']['fields'][0]['value'] += "* <@" + user + "> " + " ".join([medals[medal_index] + " " + str(medal_count) for medal_index, medal_count in medal_counts[game][user].items()]) + "\n"
	discord_helper.send_request(discord_helper.POST, homeworkURL, constants.headers, json.dumps(data))

def get_date_from_game_num(start_date, game_number):
	game_number = int(game_number)
	start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	return (start_date + datetime.timedelta(days=game_number)).strftime('%-m/%d/%Y')

def get_game_num_from_game_date(game_date, start_date):
	game_date = datetime.datetime.strptime(game_date, '%m/%d/%Y')
	start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
	return str((game_date - start_date).days)

def is_valid_result(result):
	return len(result) == 1 and len(result[0]) == 2

def add_score(scores, game_name, user_id, game_number, game_score):
	if game_name not in scores:
		scores[game_name] = {}
	if user_id not in scores[game_name]:
		scores[game_name][user_id] = {}
	if game_number in scores[game_name][user_id]:
		# Return early so we avoid hitting the "did not finish" logic
		return
	scores[game_name][user_id][game_number] = game_score

	if game_name == CROSSWORD:
		prev_game_number = datetime.datetime.strftime((datetime.datetime.strptime(game_number, "%m/%d/%Y") - datetime.timedelta(1)), "%-m/%d/%Y")
	else:
		prev_game_number = str(int(game_number) - 1)
	if prev_game_number not in scores[game_name][user_id] and len(scores[game_name][user_id]) > 1:
		if game_name == CROSSWORD:
			min_game_num = datetime.datetime.strftime(min([datetime.datetime.strptime(x, '%m/%d/%Y') for x in scores[game_name][user_id].keys()]), "%-m/%d/%Y")
		else:
			min_game_num = str(min([int(x) for x in scores[game_name][user_id].keys()]))
		if game_number != min_game_num:
			add_score(scores, game_name, user_id, prev_game_number, DID_NOT_FINISH_SCORE)

if last_message_id != "":
	messages = discord_helper.send_request(discord_helper.GET, homeworkURL+"?after="+last_message_id+"&limit=100", constants.headers).json()
else:
	messages = discord_helper.send_request(discord_helper.GET, homeworkURL+"?limit=100", constants.headers).json()
	import time
	new_messages = [x for x in messages]
	while len(messages) % 100 == 0:
		time.sleep(1)
		new_messages = discord_helper.send_request(discord_helper.GET, homeworkURL+"?before="+new_messages[-1]['id']+"&limit=100", constants.headers).json()
		messages += new_messages

messages = [x for x in messages]
for message in messages[::-1]:
	most_recent_message_id = message['id']
	# Ignore messages by this bot
	if message['author']['id'] == TOKENS['bot_id']:
		continue
	# Check the message
	user_id = message['author']['id']

	# Wordle
	wordle_result = re.findall('Wordle ([0-9,]+).*?([0-9xX]{1})/[0-9]{1}', message['content'])
	if is_valid_result(wordle_result):
		game_number = wordle_result[0][0].replace(",", "")
		game_score = wordle_result[0][1]
		if game_score.lower() == 'x':
			game_score = '7'
		game_score = int(game_score)
		add_score(SCORES, WORDLE, user_id, game_number, game_score)

	# Connections
	connections_result = re.findall('Connections {0,1}\nPuzzle \#([0-9]+)\n([' + '.'.join(connections_squares) + '\n]+)', message['content'])
	if is_valid_result(connections_result):
		game_number = connections_result[0][0]
		game_blocks = [x for x in connections_result[0][1].split('\n') if x]
		game_score = 0
		for line in game_blocks:
			if not(any([line == 4*block for block in connections_squares])):
				game_score += 1
			else:
				game_score -= 1
		add_score(SCORES, CONNECTIONS, user_id, game_number, game_score+4)

	# Strands
	strands_result = re.findall('Strands \#([0-9]+)\n.*\n.*?([' + ''.join(strands_emojis) + '\n]+)', message['content'])
	if is_valid_result(strands_result):
		game_number = strands_result[0][0]
		game_emojis = strands_result[0][1].replace('\n', '')
		game_score = len([x for x in game_emojis if x == '💡'])
		add_score(SCORES, STRANDS, user_id, game_number, game_score)

	# Crossword
	crossword_result = re.findall('I solved the (.*?) New York Times Mini Crossword in (.*?)\!', message['content'])
	if is_valid_result(crossword_result):
		game_number = crossword_result[0][0]
		game_score = crossword_result[0][1]
		game_score = int(game_score.split(":")[-1]) + (60*int(game_score.split(":")[-2]))
		add_score(SCORES, CROSSWORD, user_id, game_number, game_score)

# Determine newly completed games
newly_completed_games = {}
for game in SCORES:
	if game not in COMPLETED_GAMES:
		COMPLETED_GAMES[game] = []
	_user = list(SCORES[game].keys())[0]
	for game_number in SCORES[game][_user]:
		if all([game_number in SCORES[game][curr_user] for curr_user in SCORES[game]]) and game_number not in COMPLETED_GAMES[game]:
			COMPLETED_GAMES[game].append(game_number)
			if game not in newly_completed_games:
				newly_completed_games[game] = []
			newly_completed_games[game].append(game_number)

# Handle completed games
for game in newly_completed_games:
	for game_number in newly_completed_games[game]:
		message_title = game + " " + game_number + " completed!"
		data = discord_helper.get_embedded_messaged_template(title=message_title)
		for medal in medals:
			data['embed']['fields'].append({'name': medal, 'value': '', 'inline': False})
		temp_scores = defaultdict(lambda: [])
		for user in SCORES[game]:
			if SCORES[game][user][game_number] == DID_NOT_FINISH_SCORE:
				_score = 1
				_found_scores = [SCORES[game][x][game_number] for x in SCORES[game].keys() if isinstance(SCORES[game][x][game_number], int)]
				if _found_scores:
					_score += max(_found_scores)
			else:
				_score = SCORES[game][user][game_number]
			temp_scores[_score].append(user)
		score_list = list(temp_scores.keys())
		score_list.sort()
		users_accounted_for = 0
		for _score in score_list:
			data['embed']['fields'][users_accounted_for]['name'] += " (" + str(_score) + ")"
			data['embed']['fields'][users_accounted_for]['value'] += "\n".join(["<@" + _id + ">" for _id in temp_scores[_score]])
			users_accounted_for += len(temp_scores[_score])
		data['embed']['fields'] = [x for x in data['embed']['fields'] if x['value']]
		discord_helper.send_request(discord_helper.POST, homeworkURL, constants.headers, json.dumps(data))

# Handle completed days
derived_completions = defaultdict(lambda: 0)
for game in COMPLETED_GAMES:
	for game_date in COMPLETED_GAMES[game]:
		if game == "Wordle":
			game_date = get_date_from_game_num(WORDLE_START_DATE, game_date)
		if game == "Connections":
			game_date = get_date_from_game_num(CONNECTIONS_START_DATE, game_date)
		if game == STRANDS:
			game_date = get_date_from_game_num(STRANDS_START_DATE, game_date)
		derived_completions[game_date] += 1
for date in derived_completions:
	if derived_completions[date] == len(list(COMPLETED_GAMES.keys())) and date not in COMPLETED_DAYS['days']:
		wordle_game_num = get_game_num_from_game_date(date, WORDLE_START_DATE)
		connections_game_num = get_game_num_from_game_date(date, CONNECTIONS_START_DATE)
		strands_game_num = get_game_num_from_game_date(date, STRANDS_START_DATE)
		# Get Rankings
		points = defaultdict(lambda: 0)
		medal_counts = defaultdict(lambda: defaultdict(lambda: 0))
		for game in SCORES.keys():
			temp_scores = defaultdict(lambda: [])
			if game == 'Wordle':
				game_number = wordle_game_num
			elif game == 'Connections':
				game_number = connections_game_num
			elif game == STRANDS:
				game_number = strands_game_num
			else:
				game_number = date
			for user in SCORES[game]:
				if SCORES[game][user][game_number] == DID_NOT_FINISH_SCORE:
					_score = 1
					_found_scores = [SCORES[game][x][game_number] for x in SCORES[game].keys() if isinstance(SCORES[game][x][game_number], int)]
					if _found_scores:
						_score += max(_found_scores)
				else:
					_score = SCORES[game][user][game_number]
				temp_scores[_score].append(user)
			score_list = list(temp_scores.keys())
			score_list.sort()
			users_accounted_for = 0
			for _score in score_list:
				game_points = len(list(SCORES[game].keys())) - users_accounted_for
				for id in temp_scores[_score]:
					points[id] += game_points
					medal_counts[id][users_accounted_for] += 1
				users_accounted_for += len(temp_scores[_score])
		temp_scores = defaultdict(lambda: [])
		for id in points:
			temp_scores[points[id]].append(id)
		ranks = defaultdict(lambda: [])
		users_accounted_for = 0
		scores_list = list(temp_scores.keys())
		scores_list.sort()
		for score in scores_list[::-1]:
			ranks[users_accounted_for] += [(x, score) for x in temp_scores[score]]
			users_accounted_for += len(temp_scores[score])
		medal_count_strings = defaultdict(lambda: "")
		for _id in medal_counts:
			keys = list(medal_counts[_id].keys())
			keys.sort()
			for key in keys:
				medal_count_strings[_id] += medals[key] * medal_counts[_id][key]
		# Get embedded message
		message_title = date + " games completed!"
		data = discord_helper.get_embedded_messaged_template(title=message_title)
		for medal in medals:
			data['embed']['fields'].append({'name': medal, 'value': '', 'inline': False})
		users_accounted_for = 0
		for _rank in ranks:
			data['embed']['fields'][users_accounted_for]['value'] += "\n".join(["<@" + _id + "> " + medal_count_strings[_id] for _id, _ in ranks[_rank]])
			if '(' not in data['embed']['fields'][users_accounted_for]['name']:
				data['embed']['fields'][users_accounted_for]['name'] += " (" + str(ranks[_rank][0][1]) + ")"
			users_accounted_for += len(ranks[_rank])
		data['embed']['fields'] = [x for x in data['embed']['fields'] if x['value']]
		discord_helper.send_request(discord_helper.POST, homeworkURL, constants.headers, json.dumps(data))
		COMPLETED_DAYS['days'].append(date)
		count_medals(COMPLETED_GAMES, SCORES)

json_helper.dump(SCORES, 'database/scores.json')
json_helper.dump(COMPLETED_GAMES, 'database/completed_games.json')
json_helper.dump(COMPLETED_DAYS, 'database/completed_days.json')
if most_recent_message_id:
	constants.set_last_message_id(most_recent_message_id)
