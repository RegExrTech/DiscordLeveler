import json_helper

TOKENS = json_helper.get_db("Utils/tokens.json")

headers = {"Authorization":"Bot {}".format(TOKENS["token"]),
	"User-Agent":"SwapBot (https://www.regexr.tech, v0.1)",
	"Content-Type":"application/json"}

baseURL = "https://discordapp.com/api/channels/{}/messages"

last_message_id_fname = "Utils/last_message_id.txt"

f = open(last_message_id_fname, 'r')
last_message_id = f.read()
f.close()

def set_last_message_id(last_message_id):
	f = open(last_message_id_fname, 'w')
	f.write(last_message_id)
	f.close()
