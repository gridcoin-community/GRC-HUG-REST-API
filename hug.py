from bs4 import BeautifulSoup
import gzip
import hug
import json
import umsgpack
import numpy as np
from pathlib import Path
import pendulum
import requests
import sys
import time
import xmltodict

from Config.PROTOC_OUTPUT import protobuffer_pb2

# Configured in the gridcoinresearch.conf file:
rpcuser="rpcusernametesting1337"
rpcpassword="rpcpaswordtesting1337"
rpcip="127.0.0.1"
rpcport="9332"

# Variables for use in all HUG functions:
rpc_url="http://"+rpcuser+":"+rpcpassword+"@"+rpcip+":"+rpcport
headers = {'content-type': 'application/json'}
api_auth_key = "123abc" # Change to whatever you want - improves security!

# API preferences
hide_ip_addresses=True # IP addresses are shown in several commands, if true we'll hide this information!
WORKER_COUNT = 4 # Add CPUs & increase this value to supercharge processing downloaded project XML data!
MAX_STATS_LIFETIME = 21600 # Max seconds since last

def request_json(input_method, input_parameters, timer, api_key):
	"""
	Request JSON data from the GRC full node, given the target command & relevant input parameters.
	More info: http://docs.python-.org/en/master/
	"""

	if (api_key != api_auth_key):
		# User provied an invalid API key!
		return {'success': False, 'api_key': False, 'time_taken': timer, 'hug_error_message': 'Invalid API key input.'}

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
			return {'success': False, 'api_key': True, 'time_taken': timer, 'hug_error_message': 'GRC client error.'}
		else:
			# Success! Let's return the requested data!
			result = requested_data.json()['result']

			if (hide_ip_addresses == True):
				# API operator wants the IP addresses hidden!
				if (input_method == "getinfo" or input_method == "getnetworkinfo"):
					# Hiding IP within getinfo and getnetworkinfo results
					result['ip'] = "ip.ip.ip.ip"
				if (input_method == "getpeerinfo"):
					# Hiding each connected peer's IP & Port
					for peer in result:
						peer['addr'] = "ip.ip.ip.ip"

				return {'success': True, 'api_key': True, 'result': result, 'time_taken': timer, 'hug_error_message': ''}
			else:
				return {'success': True, 'api_key': True, 'result': result, 'time_taken': timer, 'hug_error_message': ''}
	except requests.exceptions.ConnectionError:
		# Connection to the Gridcoin node failed, return failure
		return {'success': False, 'api_key': True, 'time_taken': timer, 'hug_error_message': 'GRC client error.'}

def return_json_file_contents(filename):
	"""
	Simple function for returning the contents of the input JSON file
	"""
	try:
		with open(filename) as json_data:
			return json.load(json_data)
	except IOError:
		print("File not found: "+filename)
		return None

def read_msgpack_bin_from_disk(filename):
	"""
	Extract stored msgpack data from disk
	"""
	try:
		with open(filename, 'rb') as msgpack_data:
			return umsgpack.load(msgpack_data)
	except IOError:
		print("File not found: "+filename)
		return None

def open_protobuffer_from_file(filename):
	"""
	Read the existing project file
	"""
	try:
		with open(filename, "rb") as protobuf_data:
			project = protobuffer_pb2.Project() # Defines the protobuffer!
			project.ParseFromString(protobuf_data.read())
			return project
	except IOError:
		print("File not found: "+filename)
		return None

def initialize_project_data():
	"""Initialise BOINC project statistics into memory."""
	init_project = return_json_file_contents('./Config/init_projects.json')

	"""
	[
		{
		"project_name": "SETI@Home",
		"user_gz_url": "https://setiweb.ssl.berkeley.edu/stats/user.gz"
		},
		...
	]
	"""
	all_projects_json_list = []
	all_projects_msgpack_list = []
	all_projects_protobuffer_list = []
	all_projects_time_taken_list = []
	for project in init_project:
		"""Iterating over all projects in config file"""
		print("Reading {} files from disk".format(project['project_name']))

		before_json_read = pendulum.now() # Getting the time
		all_projects_json_list.append({'project_name': project['project_name'], 'json': return_json_file_contents("./STATS_DUMP/"+project['project_name']+".json")})
		before_msgpack_read = pendulum.now() # Getting the time
		all_projects_msgpack_list.append({'project_name': project['project_name'], 'msgpack': read_msgpack_bin_from_disk("./STATS_DUMP/"+project['project_name']+".msgpked_bin")})
		before_protobuffer_read = pendulum.now() # Getting the time
		all_projects_protobuffer_list.append({'project_name': project['project_name'], 'protobuffer': open_protobuffer_from_file("./STATS_DUMP/"+project['project_name']+".proto_bin")})
		complete_project_read = pendulum.now() # Getting the time
		all_projects_time_taken_list.append({'project_name': project['project_name'], 'time_to_read_json': before_json_read.diff(before_msgpack_read).in_words(), 'time_to_read_msgpack': before_msgpack_read.diff(before_protobuffer_read).in_words(), 'time_to_read_protobuffer': before_protobuffer_read.diff(complete_project_read).in_words()})
		print("---")

	# We're ready to store the retrieved project contents into memory
	return all_projects_json_list, all_projects_msgpack_list, all_projects_protobuffer_list, all_projects_time_taken_list

#####################
"""
# Initializing the BOINC data!
Returns json, msgpack and protobuffer project contents in lists.
"""
project_json_list, project_msgpack_list, project_porotobuf_list, project_time_taken_list = initialize_project_data()

print(project_time_taken_list)

#####################

@hug.get(examples='api_key=API_KEY&format=JSON')
def user_stats(api_key: hug.types.text, format: hug.types.text, hug_timer=3):
	"""Provide BOINC project user statistics. Format can be either JSON or MSGPACK"""

	if (api_key != api_auth_key):
		# User provied an invalid API key!
		return {'success': False, 'api_key': False, 'took': float(hug_timer), 'hug_error_message': 'Invalid API key input.'}

	if format == "JSON":
		return {'project_json_list': project_json_list, 'success': True, 'api_key': True, 'took': float(hug_timer)}
	elif format == "MSGPACK":
		return {'project_msgpack_list': project_msgpack_list, 'success': True, 'api_key': True, 'took': float(hug_timer)}
		"""
		msgpacked_data = []
		for project in fully_processed_project_data:
			msgpacked_contents = umsgpack.packb(project['json_data'])
			#msgpacked_contents = msgpack.packb(project['json_data'], use_bin_type=True)
			msgpacked_data.append({'project': project['project_name'], 'msgpacked_data': str(msgpacked_contents)})

		return {'project_msgpack': msgpacked_data, 'success': True, 'api_key': True, 'took': float(hug_timer)}
		"""
	elif format == "PROTOBUF":
		return {'project_porotobuf_list': project_porotobuf_list, 'success': True, 'api_key': True, 'took': float(hug_timer)}
	else:
		return {'success': False, 'api_key': True, 'took': float(hug_timer), 'hug_error_message': 'Invalid format requested. Choose from JSON, MSGPACK and '}

#####################

@hug.get(examples='api_key=API_KEY, function=FUNCTION_NAME')
def grc_command(api_key: hug.types.text, function: hug.types.text, hug_timer=3):
	"""Generic HUG function for all read-only Gridcoin commands which don't require any input parameters."""
	valid_functions = [
		# Only add read-only parameter-free gridcoinresearch commands to this list
		"beaconreport",
		"currentneuralhash",
		"currentneuralreport",
		"getmininginfo",
		"neuralreport",
		"superblockage",
		"upgradedbeaconreport",
		"validcpids",
		"getbestblockhash",
		"getblockchaininfo",
		"getblockcount",
		"getconnectioncount",
		"getdifficulty",
		"getinfo",
		"getnettotals",
		"getnetworkinfo",
		"getpeerinfo",
		"getrawmempool",
		"listallpolldetails",
		"listallpolls",
		"listpolldetails",
		"listpolls",
		"networktime",
		"getwalletinfo"
	]

	if (function in valid_functions):
		# User requested a valid read-only parameter-free GRC function
		return request_json(function, None, hug_timer, api_key)
	else:
		# User requested an invalid function
		return {'success': False, 'api_key': True, 'took': float(hug_timer), 'hug_error_message': 'Invalid GRC command requested by user.'}

"""
NOTE: Below this point the HUG functions require user input!
"""

@hug.get(examples='api_key=API_KEY, txid=transactionId')
def getrawtransaction(api_key: hug.types.text, txid: hug.types.text, hug_timer=3):
	"""getrawtransaction <txid> [verbose=bool]"""
	# Valid API Key!
	parameters = {
	'txid': txid
	}
	return request_json("getrawtransaction", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, address=GRCAddress, minconf=1')
def getreceivedbyaddress(api_key: hug.types.text, address: hug.types.text, minconf: hug.types.number=1, hug_timer=3):
	"""getreceivedbyaddress <Gridcoinaddress> [minconf=1]"""
	# Valid API Key!
	parameters = {
	'Gridcoinaddress': address,
	'minconf': minconf
	}
	return request_json("getreceivedbyaddress", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, txid=grctxid')
def gettransaction(api_key: hug.types.text, txid: hug.types.text, hug_timer=3):
	"""gettransaction "txid" """
	# Valid API Key!
	parameters = {
	'txid': txid
	}
	return request_json("gettransaction", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, blockhash=grctxid, target_confirmations=1, includeWatchonly=True')
def listsinceblock(api_key: hug.types.text, blockhash: hug.types.text, target_confirmations: hug.types.number=1, hug_timer=3):
	"""listsinceblock ( "blockhash" target-confirmations includeWatchonly)"""
	# Valid API Key!
	parameters = {
	'blockhash': txid,
	'target-confirmations': target_confirmations,
	'includeWatchonly': includeWatchonly
	}
	return request_json("listsinceblock", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, address=grcaddress')
def validateaddress(api_key: hug.types.text, address: hug.types.text, hug_timer=3):
	"""validateaddress <gridcoinaddress>"""
	parameters = {
	'gridcoinaddress': address
	}
	return request_json("validateaddress", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, pubkey=grctxid')
def validatepubkey(api_key: hug.types.text, pubkey: hug.types.text, hug_timer=3):
	"""validatepubkey <gridcoinpubkey>"""
	parameters = {
	'gridcoinpubkey': pubkey
	}
	return request_json("validatepubkey", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, address=grcaddress, signature=examplesigtext, message=examplemessage')
def verifymessage(api_key: hug.types.text, signature: hug.types.text, message: hug.types.text, hug_timer=3):
	"""verifymessage <Gridcoinaddress> <signature> <message>"""
	parameters = {
	'Gridcoinaddress': address,
	'signature': signature,
	'message': message
	}
	return request_json("verifymessage", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, hash=grctxid, extra_info=true')
def getblock(api_key: hug.types.text, hash: hug.types.text, extra_info: hug.types.smart_boolean=0, hug_timer=3):
	"""getblock <hash> [bool:txinfo]"""
	parameters = {
	'hash': hash,
	'bool:txinfo': extra_info
	}
	return request_json("getblock", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, index=50')
def getblockhash(api_key: hug.types.text, index: hug.types.number, hug_timer=3):
	"""getblockhash <index>"""
	parameters = {
	'index': index
	}
	return request_json("getblockhash", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, index=50')
def showblock(api_key: hug.types.text, index: hug.types.number, hug_timer=3):
	"""showblock <index>"""
	parameters = {
	'index': index
	}
	return request_json("showblock", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, pollname=whitelist_poll')
def votedetails(api_key: hug.types.text, pollname: hug.types.text, hug_timer=3):
	"""votedetails <pollname>"""
	parameters = {
	'pollname': pollname
	}
	return request_json("votedetails", parameters, hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, cpid=grctxid')
def beaconstatus(api_key: hug.types.text, cpid: hug.types.text, hug_timer=3):
	"""beaconstatus [cpid]"""
	parameters = {
	'cpid': cpid
	}
	return request_json("beaconstatus", parameters, hug_timer, api_key)
