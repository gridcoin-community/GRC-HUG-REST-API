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
			"id": 0
		}
	else:
		# Include provided input poarameters in payload
		payload = {
			"method": input_method,
			"params": input_parameters,
			"jsonrpc": "2.0",
			"id": 0
		}

	try:
		# Attempt to contact GRC node via JSON RPC
		requested_data = requests.get(rpc_url, data=json.dumps(dict(payload)), headers=headers)
		print(" - - - ")
		print(requested_data.content)
		print("---")
		if requested_data.status_code is not 200:
			# 200 means success, if we get anything else we will return a controlled failure
			return {'success': False, 'api_key': True, 'requested_data.status_code':requested_data.status_code, 'time_taken': timer, 'hug_error_message': 'GRC client != 200 error.'}
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
		return {'success': False, 'api_key': True, 'time_taken': timer, 'hug_error_message': 'GRC client connection error.'}

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

@hug.get(examples='api_key=API_KEY&function=FUNCTION_NAME')
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
		return {'success': False, 'api_key': True, 'took': float(hug_timer), 'hug_error_message': 'Invalid GRC command requested by user. Use: {}'.format(', '.join(valid_functions))}

"""
NOTE: Below this point the HUG functions require user input!
"""

@hug.get(examples='api_key=API_KEY&txid=transactionId')
def getrawtransaction(api_key: hug.types.text, txid: hug.types.text, hug_timer=3):
	"""getrawtransaction <txid> [verbose=bool]"""
	return request_json("getrawtransaction", [txid], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&address=GRCAddress&minconf=1')
def getreceivedbyaddress(api_key: hug.types.text, address: hug.types.text, minconf: hug.types.number=1, hug_timer=3):
	"""getreceivedbyaddress <Gridcoinaddress> [minconf=1]"""
	return request_json("getreceivedbyaddress", [address, minconf], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY, txid=grctxid')
def gettransaction(api_key: hug.types.text, txid: hug.types.text, hug_timer=3):
	"""gettransaction "txid" """
	return request_json("gettransaction", [txid], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&blockhash=grctxid&target_confirmations=1&includeWatchonly=True')
def listsinceblock(api_key: hug.types.text, blockhash: hug.types.text, target_confirmations: hug.types.number=1, includeWatchonly: hug.types.smart_boolean=True, hug_timer=3):
	"""listsinceblock ( "blockhash" target-confirmations includeWatchonly)"""
	return request_json("listsinceblock", [blockhash, target_confirmations, includeWatchonly], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&address=grcaddress')
def validateaddress(api_key: hug.types.text, address: hug.types.text, hug_timer=3):
	"""validateaddress <gridcoinaddress>"""
	return request_json("validateaddress", [address], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&gridcoinpubkey=grctxid')
def validatepubkey(api_key: hug.types.text, gridcoinpubkey: hug.types.text, hug_timer=3):
	"""validatepubkey <gridcoinpubkey>"""
	return request_json("validatepubkey", [gridcoinpubkey], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&address=grcaddress&signature=examplesigtext&message=examplemessage')
def verifymessage(api_key: hug.types.text, signature: hug.types.text, message: hug.types.text, hug_timer=3):
	"""verifymessage <Gridcoinaddress> <signature> <message>"""
	return request_json("verifymessage", [address, signature, message], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&index=50')
def getblockhash(api_key: hug.types.text, index: hug.types.number, hug_timer=3):
	"""getblockhash <index>"""
	return request_json("getblockhash", [index], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&index=50')
def showblock(api_key: hug.types.text, index: hug.types.number, hug_timer=3):
	"""showblock <index>"""
	return request_json("showblock", [index], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&pollname=whitelist_poll')
def votedetails(api_key: hug.types.text, pollname: hug.types.text, hug_timer=3):
	"""votedetails <pollname>"""
	return request_json("votedetails", [pollname], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&cpid=BOINC_CPID')
def beaconstatus(api_key: hug.types.text, cpid: hug.types.text, hug_timer=3):
	"""beaconstatus [cpid]"""
	return request_json("beaconstatus", [cpid], hug_timer, api_key)

@hug.get(examples='api_key=API_KEY&hash=grctxid&txinfo_bool=true')
def getblock(api_key: hug.types.text, hash: hug.types.text, extra_info: hug.types.smart_boolean=False, hug_timer=3):
	"""getblock <hash> [bool:txinfo]"""
	return request_json("getblock", [hash, txinfo_bool], hug_timer, api_key)
