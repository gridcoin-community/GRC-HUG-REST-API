from bs4 import BeautifulSoup
import gzip
import hug
import json
import msgpack
from pathlib import Path
import pendulum
import requests
import sys
import time
import xmltodict

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
	"""Request JSON data from the GRC full node, given the target command & relevant input parameters.
	   More info: http://docs.python-.org/en/master/"""

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

def return_json_file_contents(json_file_name):
	"""
	Simple function for returning the contents of the input JSON file
	"""
	with open(json_file_name) as json_contents:
		return json.load(json_contents)

def scrape_gridcoinstats_for_whitelist():
	"""
	A function to scrape gridcoinstats.eu for the active whitelist.
	"""
	scraped_page = requests.get("https://gridcoinstats.eu/project")
	if scraped_page.status_code == 200:
		soup = BeautifulSoup(scraped_page.text, 'html.parser')
		whitelist_table = soup.find('table', attrs={'id': 'whiteProjects'})
		whitelist_rows = whitelist_table.findAll('span', attrs={'class': 'hideOnMobile'})

		whitelisted_urls = []
		for row in whitelist_rows:
			temp_str = str(row)
			tsl = temp_str.split('<a href="')
			url = (tsl[1].split('" target'))[0]

			whitelisted_urls.append(url)
		return whitelisted_urls
	else:
		return None

def write_json_to_disk(filename, json_data):
	"""
	When called, write the json_data to a json file.
	We will end up with many data_*.json files.
	These files will be merged using jq.
	"""
	with open(filename, 'w') as outfile:
		json.dump(json_data, outfile)

def extract_xml_step(xml_row):
	"""
	Multiprocessing the extraction of key info from selected xml items!
	TODO: Handle varying XML format (different contents, validation, etc..)
	"""
	if (xml_row.get('id', None) != None) and (xml_row.get('total_credit', None) != None) and (xml_row.get('expavg_credit', None) != None) and (xml_row.get('cpid', None) != None):
		#print("attr exists")
		if (float(xml_row['expavg_credit']) > 1):
			# To save resources we're only going to provide stats for active users
			return {'id': xml_row['id'], 'total_credit': xml_row['total_credit'], 'expavg_credit': xml_row['expavg_credit'], 'cpid': xml_row['cpid']}
		else:
			# Filtered out
			return None
	else:
		print("attr doesn't exist")
		# filtered out
		return None

def download_extract_stats(project_name, project_url):
	"""
	Download an xml.gz, extract gz, parse xml, reduce & return data.
	"""
	file_path = "./STATS_DUMP/"+project_name+".json"
	existing_file_check = Path(file_path)
	if existing_file_check.is_file():
		print("File existed!")
		"""File exists - check its contents"""
		existing_json = return_json_file_contents(file_path)

		now = pendulum.now() # Getting the time (SIGIR)
		current_timestamp = int(round(now.timestamp())) # Converting to timestamp (SIGIR)

		if (current_timestamp - int(existing_json['timestamp']) < MAX_STATS_LIFETIME):
			"""Data is still valid - let's return it instead of fetching it!"""
			print("Within lifetime")
			return existing_json['json_data']
		else:
			"""No existing file"""
			print("{} stats too old - downloading fresh copy!".format(project_name))

	"""No existing file - let's download and process it!"""
	print("Downloading {}".format(project_name))

	downloaded_file = requests.get(project_url, stream=True)
	if downloaded_file.status_code == 200:
		# Worked
		if '.gz' in project_url:
			# Compressed!
			with gzip.open(downloaded_file.raw, 'rb') as uncompressed_file:
				file_content = xmltodict.parse(uncompressed_file.read())
		else:
			# Not compressed!
			file_content = xmltodict.parse(downloaded_file.text) # Not confirmed

		# print("len: {}".format(len(file_content['users']['user'])))

		#pool = Pool(processes=WORKER_COUNT) # 4 workers
		#pool_xml_data = pool.map(extract_xml_step, file_content['users']['user']) # Deploy the pool workers
		#pool.terminate()
		#filter(None, pool_xml_data) # Removing failed elements

		xml_data = []
		for user in file_content['users']['user']:
			xml_contents = extract_xml_step(user)
			if xml_contents == None:
				# Filter it out
				continue
			else:
				# Success!
				xml_data.append(xml_contents)

		now = pendulum.now() # Getting the time (SIGIR)
		current_timestamp = int(round(now.timestamp())) # Converting to timestamp (SIGIR)
		write_json_to_disk('./STATS_DUMP/' + project_name + '.json', {'json_data': xml_data, 'timestamp': current_timestamp}) # Storing to disk

		#msg_packed_results = msgpack.packb(xml_data, use_bin_type=True)
		return xml_data
	else:
		print("ERROR: {}".format(project_name))
		# Didn't work
		return None

#####################

def initialize_project_data():
	"""Initialise BOINC project statistics into memory."""
	initial_project_json = return_json_file_contents('init_projects.json')

	"""
	[
		{
		"project_name": "SETI@Home",
		"user_gz_url": "https://setiweb.ssl.berkeley.edu/stats/user.gz"
		},
		...
	]
	"""
	processed_project_data = []

	for project in initial_project_json: # TODO: REMOVE ':3'
		temp_project_holder = project # Can we just reference project?
		print("Checking {}".format(project['project_name']))
		json_data = download_extract_stats(project['project_name'], project['user_gz_url'])
		if (json_data != None):
			temp_project_holder['json_data'] = json_data
		else:
			print("Failed to download: {}".format(project['project_name']))
			continue

		processed_project_data.append(temp_project_holder)

	return processed_project_data

fully_processed_project_data = initialize_project_data()

#####################

@hug.get(examples='api_key=API_KEY&format=JSON')
def user_stats(api_key: hug.types.text, format: hug.types.text, hug_timer=3):
	"""Provide BOINC project user statistics. Format can be either JSON or MSGPACK"""

	if (api_key != api_auth_key):
		# User provied an invalid API key!
		return {'success': False, 'api_key': False, 'took': float(hug_timer), 'hug_error_message': 'Invalid API key input.'}

	if format == "JSON":
		return {'project_json': fully_processed_project_data, 'success': True, 'api_key': True, 'took': float(hug_timer)}
	elif format == "MSGPACK":
		msgpacked_data = []
		for project in fully_processed_project_data:
			msgpack_contents = msgpack.packb(project['json_data'], use_bin_type=True)
			msgpacked_data.append({'project': project['project_name'], 'msgpacked_data': str(msgpack_contents)})

		return {'project_msgpack': msgpacked_data, 'success': True, 'api_key': True, 'took': float(hug_timer)}

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
