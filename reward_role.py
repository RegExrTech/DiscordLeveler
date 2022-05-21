import sys
sys.path.insert(0, 'Utils')
import requests
import json

import json_helper
import constants
import discord_helper

TOKENS = constants.TOKENS
role_ids = TOKENS['role_ids']

scrapeURL = constants.baseURL.format(TOKENS["channels"]["levels"])
roleURL = "https://discordapp.com/api/guilds/" + TOKENS['server_id'] + "/members/{}/roles/{}"

def get_last_role_id(role_id, role_ids):
	ranks = [int(x) for x in list(role_ids.keys())]
	ranks.sort()
	ranks = [str(x) for x in ranks]
	last_role_id = ""
	for rank in ranks:
		if role_id == role_ids[rank]:
			break
		last_role_id = role_ids[rank]
	return last_role_id

last_message_id = constants.last_message_id
most_recent_message_id = ""

if last_message_id != "":
	messages = discord_helper.send_request(discord_helper.GET, scrapeURL+"?after="+last_message_id+"&limit=100", constants.headers).json()
else:
	messages = discord_helper.send_request(discord_helper.GET, scrapeURL+"?limit=100", constants.headers).json()
for message in messages:
	# Store the first message's ID as this round's most recent message ID
	if most_recent_message_id == "":
		most_recent_message_id = message['id']
	# If we've already seen this message, end early
	if last_message_id == most_recent_message_id:
		break
	# Ignore messages by this bot
	if message['author']['id'] == TOKENS['bot_id']:
		continue
	# Check the message
	user_id = message['mentions'][0]['id']
	level = message['content'].split("level ")[1].split("!")[0]
	if level in role_ids:
		new_role_id = role_ids[level]
		last_role_id = get_last_role_id(new_role_id, role_ids)
		discord_helper.send_request(discord_helper.PUT, roleURL.format(user_id, new_role_id), constants.headers)
		if last_role_id != "":
			discord_helper.send_request(discord_helper.DELETE, roleURL.format(user_id, last_role_id), constants.headers)
		message_data = {'content': "Congratulations on reaching level " + level + ", <@"+user_id+">! Take a look at your profile to see your shiny new rank!"}
		discord_helper.send_request(discord_helper.POST, scrapeURL, constants.headers, json.dumps(message_data))
if most_recent_message_id == "":
	most_recent_message_id = last_message_id
constants.set_last_message_id(most_recent_message_id)
