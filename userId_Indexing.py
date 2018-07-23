import json

def write_json_to_disk(filename, json_data):
	"""
	When called, write the json_data to a json file.
	"""
	with open(filename, 'w') as outfile:
		json.dump(json_data, outfile)

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

overall_boinc_project_cpid_index = {} # {'cpid': [{'project': userId}], 'cpid':...}

project_list = return_json_file_contents('./Config/init_projects.json') # [{"project_name": "SETI@Home","user_gz_url": "https://setiweb.ssl.berkeley.edu/stats/user.gz"}, ...]

for project in project_list:
	# Iterate over projects included in the init_projects.json file
    project_json = return_json_file_contents("./STATS_DUMP/"+project['project_name']+".json")['json_data']

    for user in project_json:
        # Iterating over each user within each project's JSON files
        if user['cpid'] in overall_boinc_project_cpid_index.items():
            # CPID already spotted
            overall_boinc_project_cpid_index[str(user['cpid'])].append({'project': project['project_name'], 'id': user['id'], 'total_credit': user['total_credit'], 'expavg_credit': user['expavg_credit']})
        else:
            # Found a new CPID
            overall_boinc_project_cpid_index[str(user['cpid'])] = [{'project': project['project_name'], 'id': user['id'], 'total_credit': user['total_credit'], 'expavg_credit': user['expavg_credit']}]

write_json_to_disk("./INDEXED_STATS_DUMP/overall_boinc_project_cpid_index.json", overall_boinc_project_cpid_index)
