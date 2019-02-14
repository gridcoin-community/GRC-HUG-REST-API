import gzip
import json
import umsgpack
import numpy as np
from pathlib import Path
import pendulum
import requests
import sys
import time
import xmltodict
import base64

# For captn proto
from __future__ import print_function
import os
import capnp
import boinc_schema_capnp # Import our captn proto schema

# Protobuffer
from Config.PROTOC_OUTPUT import protobuffer_pb2

def write_json_to_disk(filename, json_data):
	"""
	When called, write the json_data to a json file.
	"""
	with open(filename, 'w') as outfile:
		json.dump(json_data, outfile)

def write_msgpack_bin_to_disk(filename, json_data):
	"""
	Store msgpack data as bin on disk
	"""
	with open(filename, 'wb') as f:
		umsgpack.dump(json_data, f)

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
	with open(filename, 'rb') as f:
		return umsgpack.load(f)

def extract_xml_step(xml_row):
	"""
	Multiprocessing the extraction of key info from selected xml items!
	TODO: Handle varying XML format (different contents, validation, etc..)
	"""
	if (xml_row.get('id', None) != None) and (xml_row.get('total_credit', None) != None) and (xml_row.get('expavg_credit', None) != None) and (xml_row.get('cpid', None) != None):
		#print("attr exists")
		if (float(xml_row['expavg_credit']) > 1):
			"""
			To save resources we enforce a min RAC of 1.
			Alternative: 'total_credit > 1' (Includes many inactive accounts)
			"""
			return {'id': xml_row['id'], 'total_credit': xml_row['total_credit'], 'expavg_credit': xml_row['expavg_credit'], 'cpid': xml_row['cpid']}
		else:
			# Less than min RAC - skip user.
			return None
	else:
		"""
		Filtered out - will only occur if the project has customized the contents of their user xml gz files.
		If this occurs then please raise an issue on github.
		"""
		print("WARNING: XML Attr doesn't exist!!!")
		return None

def open_protobuffer_from_file(filename):
	"""Read the existing project file"""
	try:
		with open(filename, "rb") as file:
			project = protobuffer_pb2.Project() # Defines the protobuffer!
			project.ParseFromString(file.read())
			return project
	except IOError:
		print(filename + ": File not found.  Creating a new file.")
		return None

def write_protobuffer_to_disk(filename, target):
	"""Write the project file to disk"""
	with open(filename, "wb") as file:
		file.write(target.SerializeToString())

def write_captnproto_to_disk(filename, target):
	"""Write the project file to disk"""
	#with open(filename, "wb") as file:
	#	file.write(target.SerializeToString())
    with open(filename, 'w') as file:
    	target.write(file)

def ListUsers(Project):
    """Print the users"""
    for user in Project.users:
        print(str(user.id) + " " + str(user.total_credit) + " " + str(user.expavg_credit) + " " + str(user.cpid))

def download_extract_stats(project_name, project_url, quantity_projects):
	"""
	Download an xml.gz, extract gz, parse xml, reduce & return data.
	"""
	file_path = "./STATS_DUMP/"+project_name+".json"
	need_to_download = True
	existing_file_check = Path(file_path)
	if existing_file_check.is_file():
		print("File existed!")
		"""
			File exists - check its contents
			TODO: Read msgpack | protobuffer instead of JSON?
		"""
		existing_json = return_json_file_contents("./STATS_DUMP/"+project_name+".json")
		#existing_bin = read_msgpack_bin_from_disk("./STATS_DUMP/"+project_name+".msgpked_bin")
		#existing_protobuffer = open_protobuffer_from_file("./STATS_DUMP/"+project_name+".proto_bin")

		now = pendulum.now() # Getting the time
		current_timestamp = int(round(now.timestamp())) # Converting to timestamp

		if (current_timestamp - int(existing_json['timestamp']) < MAX_STATS_LIFETIME):
			"""Data is still valid - let's return it instead of fetching it!"""
			print("Within lifetime")
			need_to_download = False
		else:
			"""No existing file"""
			print("{} stats too old - downloading fresh copy!".format(project_name))

	if (need_to_download == True):
		"""No existing file - let's download and process it!"""
		try:
			downloaded_file = requests.get(project_url, stream=True)
			print("Downloading {}".format(project_name))
			if downloaded_file.status_code == 200:
				# Worked
				with gzip.open(downloaded_file.raw, 'rb') as uncompressed_file:
					"""Opening GZ & converting XML to dict"""
					print("Downloaded {}".format(project_name))
					if project_name == "YOYO@Home":
						with gzip.open(uncompressed_file, 'rb') as extra_uncompressed_file:
							"""Opening nested GZ & converting XML to dict. TODO: Attempt this on failure to xmltodict parse?"""
							file_content = xmltodict.parse(extra_uncompressed_file.read())
					else:
						file_content = xmltodict.parse(uncompressed_file.read())

				print("Converted. Now Processing: {}".format(project_name))

				xml_data = []
				project = protobuffer_pb2.Project() # Defines the protobuffer!

			    Users = boinc_schema_capnp.Users.new_message()
			    captn_user = Users.init('user', len(file_content['users']['user'])) # Initialise an array of 'user' objects

				user_iterator = 0
				for user in file_content['users']['user']:
					user_xml_contents = extract_xml_step(user)
					if user_xml_contents == None:
						# Filter it out
						continue
					else:
						#user_xml_contents['cpid'] = str(bytes.fromhex(user_xml_contents['cpid']))
						user_xml_contents['cpid'] = str(base64.b64encode(bytes.fromhex(user_xml_contents['cpid'])))
						xml_data.append(user_xml_contents)

						current_id = np.int64(user_xml_contents['id'])
						current_total_credit = float(user_xml_contents['total_credit'])
						current_expavg_credit = float(user_xml_contents['expavg_credit'])
						current_cpid = user_xml_contents['cpid']

						# Protobuffer
						proto_user = project.users.add()
						proto_user.id = current_id
						proto_user.total_credit = current_total_credit
						proto_user.expavg_credit = current_expavg_credit
						proto_user.cpid = current_cpid

						# Captn Proto
					    captn_user[user_iterator].id = current_id
					    captn_user[user_iterator].total_credit = current_total_credit
					    captn_user[user_iterator].expavg_credit = current_expavg_credit
					    captn_user[user_iterator].cpid = current_cpid
						user_iterator += 1 # For iterating captn_user

				now = pendulum.now() # Getting the time
				current_timestamp = int(round(now.timestamp())) # Converting to timestamp

				before_json_write = pendulum.now() # Getting the time
				write_json_to_disk('./STATS_DUMP/' + project_name + '.json', {'json_data': xml_data, 'timestamp': current_timestamp}) # Storing to disk
				before_msgpack_write = pendulum.now() # Getting the time
				write_msgpack_bin_to_disk('./STATS_DUMP/' + project_name + '.msgpked_bin', {'json_data': xml_data, 'timestamp': current_timestamp}) # Storing to disk
				before_protobuf_write = pendulum.now() # Getting the time
				write_protobuffer_to_disk('./STATS_DUMP/' + project_name + '.proto_bin', project)
				after_protobuf_write = pendulum.now() # Getting the time
				before_captn_write = pendulum.now() # Getting the time
				write_captnproto_to_disk('./STATS_DUMP/' + project_name + '.captn_bin', Users)
				after_captn_write = pendulum.now() # Getting the time
				return before_json_write, before_msgpack_write, before_protobuf_write, after_protobuf_write, before_captn_write, after_captn_write

			else:
				print("ERROR: {}".format(project_name))
				# TODO: Skip this project when attempting to read from disk!
		except requests.exceptions.ConnectionError:
			print("Error connecting to {}".format(project_name))
	else:
		"""Existing file detected. skip!"""

def initialize_project_data():
	"""Initialise BOINC project statistics into memory."""
	init_project = return_json_file_contents('./Config/init_projects.json') # [{"project_name": "SETI@Home","user_gz_url": "https://setiweb.ssl.berkeley.edu/stats/user.gz"}, ...]

	all_projects_time_taken_list = []

	current_project_value = 0
	for project in init_project:
		"""Iterating over all projects in config file"""
		print("Checking : {}".format(project['project_name']))
		before_json_write, before_msgpack_write, before_protobuf_write, after_protobuf_write = download_extract_stats(project['project_name'], project['user_gz_url'], current_project_value)
		print("DUCK!")
		all_projects_time_taken_list.append({'project_name': project['project_name'], 'time_to_write_json': before_json_write.diff(before_msgpack_write).in_words(), 'time_to_write_msgpack': before_msgpack_write.diff(before_protobuf_write).in_words(), 'time_to_write_protobuf': before_protobuf_write.diff(after_protobuf_write).in_words()})
		current_project_value += 1 # Iterator for captn proto

	print(all_projects_time_taken_list)

initialize_project_data()
