import json
import hug

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

overall_boinc_project_cpid_index = return_json_file_contents('./INDEXED_STATS_DUMP/overall_boinc_project_cpid_index.json')

@hug.get(examples='api_key=API_KEY&cpid=user_cpid_string')
def get_cpid(api_key: hug.types.text, cpid: hug.types.string, hug_timer=3):
  """Get CPID details across all projects!"""
  if (api_key == api_auth_key)
  	# Valid API key!
    if cpid in overall_boinc_project_cpid_index.items():
      # Match - return the contents!
      return {'success': True, 'result': overall_boinc_project_cpid_index[cpid], 'api_key': True, 'error_message': '', 'took': float(hug_timer)}
    else:
      # No match - return a rejection.
      return {'success': False, 'api_key': True, 'error_message': 'Invalid CPID!', 'took': float(hug_timer)}
  else:
    # Invalid API key!
    return {'success': False, 'api_key': False, 'error_message': 'Invalid API key!', 'took': float(hug_timer)}
