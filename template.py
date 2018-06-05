"""
Use the following template for adding new HUG functions
NOTE:
* Don't provide non-read-only commands which can control your wallet to the public.
* The parameters will need trial & error to get right.
* If no parameters are required, use None as the parameters variable.
* Check the 'Example_Commands' folder for HUG function ideas.
"""

@hug.get(examples='api_key=API_KEY')
def template_function_name(api_key: hug.types.text, hug_timer=20):
	"""Return 'template_function_name' data from the Gridcoin Research client!"""
	if (api_key == api_auth_key):
		# Valid API Key!
        parameters = # Command specific poarameters
		response = request_json("template_function_name", parameters)
		if (response == None):
			return {'success': False, 'api_key': True}
		else:
			return {'success': True, 'api_key': True, 'result': response, 'time_taken': hug_timer}
	else:
		# Invalid API Key!
		return {'success': False, 'api_key': False}
