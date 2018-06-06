@hug.get(examples='api_key=API_KEY')
def get_info(api_key: hug.types.text, hug_timer=20):
	"""Return 'getinfo' data from the Gridcoin Research client!"""
	if (api_key == api_auth_key):
		# Valid API Key!
		response = request_json("getinfo", None)
		if (response == None):
			return {'success': False, 'api_key': True}
		else:
			return {'success': True, 'api_key': True, 'result': response, 'time_taken': hug_timer}
	else:
		# Invalid API Key!
		return {'success': False, 'api_key': False}
