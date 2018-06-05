import hug
import requests
import json

# Configured in the gridcoinresearch.conf file:
rpcuser="rpcusernametesting1337"
rpcpassword="rpcpaswordtesting1337"
rpcip="127.0.0.1"
rpcport="9332"

# Variables for use in all HUG functions:
rpc_url="http://"+rpcuser+":"+rpcpassword+"@"+rpcip+":"+rpcport
headers = {'content-type': 'application/json'}
api_auth_key = "123abc" # Change to whatever you want - improves security!

def request_json(input_method, input_parameters):
	"""Request JSON data from the GRC full node, given the target command & relevant input parameters.
	   More info: http://docs.python-requests.org/en/master/"""

	# Check for the presence of input parameter data
	if (input_parameters == None):
		# Some commands don't require any parameters
		payload = {
			"method": input_method,
			"jsonrpc": "2.0",
			"id": 1
		}
	else:
		# Include provided input poarameters in payload
		payload = {
			"method": input_method,
			"params": input_parameters,
			"jsonrpc": "2.0",
			"id": 1
		}

	try:
		# Attempt to contact GRC node via JSON RPC
		requested_data = requests.get(rpc_url, data=json.dumps(payload), headers=headers)
		if requested_data.status_code is not 200:
			# 200 means success, if we get anything else we will return a controlled failure
			return None
		else:
			# Success! Let's return the requested data!
			return requested_data.json()['result']
	except requests.exceptions.ConnectionError:
		# Connection to the Gridcoin node failed, return failure
		return None

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
