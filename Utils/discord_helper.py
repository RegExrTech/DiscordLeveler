import datetime
import time
import requests

POST = "post"
PUT = "put"
GET = "get"
PATCH = "patch"
DELETE = "delete"

def get_embedded_messaged_template(content="", title="", url="", description=""):
	data = {
		"content": content,
		"embed": {
			"title": title,
			"color": 8564590,
			"thumbnail": {},
			"image": {},
			"description": description,
			"fields": []
		}
	}
	if url:
		data['embed']['url'] = url
	return data

def send_request(type, url, headers, data={}, should_retry=True):
	valid_status_codes = [200, 204]

	if type == GET:
		r = requests.get(url, headers=headers)
#	elif type == POST:
#		r = requests.post(url, headers=headers, data=data)
#	elif type == PUT:
#		r = requests.put(url, headers=headers)
	elif type == PATCH:
		r = requests.patch(url, headers=headers, data=data)
	elif type == DELETE:
		r = requests.delete(url, headers=headers)
	else:
		return

	if r.status_code not in valid_status_codes:
		status_data = r.json()
		if 'retry_after' in status_data and should_retry:
			time.sleep((status_data['retry_after']/1000.0) + 0.1) # Add some buffer to the sleep
			return send_request(type, url, headers, data, False)
		else:
			print("Discord Failure - status: " + str(r.status_code) + " - text: " + r.text + "\nData: " + str(data))
	return r
