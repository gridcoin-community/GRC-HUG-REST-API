import json
import hug
from operator import itemgetter

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

@hug.get(examples='api_key=API_KEY&project=project_name_string&top_k=10&sort_target=RAC')
def get_top_users(api_key: hug.types.text, project: hug.types.string, top_k: hug.types.number, sort_target: hug.types.string, hug_timer=3):
	"""Retrieve the kth largest active contributors to an individual BOINC project."""
	if (api_key == api_auth_key)
		# Valid API key!
	supported_project_names = []
	list_of_supported_projects = return_json_file_contents('./Config/init_projects.json')
	for supported_project in list_of_supported_projects:
	    supported_project_names.append(supported_project['project_name'])

	if (top_k < 1 || top_k > 1000):
		# Invalid top_k value chosen!
		return {'success': False, 'api_key': True, 'error_message': 'Invalid top_k value chosen, please input a number between 1 and 1000.', 'took': float(hug_timer)}

	if sort_target not in ['expavg_credit', 'total_credit']:
		# sort target is invalid!
		return {'success': False, 'api_key': True, 'error_message': 'Invalid sort target chosen. Pick either "expavg_credit" or "total_credit"', 'took': float(hug_timer)}

	if project in supported_project_names:
	    # Match - return the contents!

		# TODO: dict key sort based on RAC | TotalCredit! Allow the user to specify?
		unordered_results = return_json_file_contents("./STATS_DUMP/"+str(project)+".json")
		ordered_results = sorted(unordered_results, key=itemgetter(str(sort_target)), reverse=True) # Sort descending

	    return {'success': True, 'result': ordered_results[:top_k], 'api_key': True, 'error_message': '', 'took': float(hug_timer)}
	else:
	    # No match - return a rejection.
	    return {'success': False, 'api_key': True, 'error_message': 'Invalid project name! Pick from: "{}"'.format(supported_project_names), 'took': float(hug_timer)}
	else:
	# Invalid API key!
	return {'success': False, 'api_key': False, 'error_message': 'Invalid API key!', 'took': float(hug_timer)}
