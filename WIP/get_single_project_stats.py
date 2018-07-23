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

@hug.get(examples='api_key=API_KEY&project=project_name_string')
def get_project_stats(api_key: hug.types.text, project: hug.types.string, hug_timer=3):
  """Retrieve all users within a specified project!"""
  if (api_key == api_auth_key)
  	# Valid API key!
	supported_project_names = []
	list_of_supported_projects = return_json_file_contents('./Config/init_projects.json')
    for supported_project in list_of_supported_projects:
        supported_project_names.append(supported_project['project_name'])

    if project in supported_project_names:
        # Match - return the contents!
        return {'success': True, 'result': return_json_file_contents("./STATS_DUMP/"+str(project)+".json"), 'api_key': True, 'error_message': '', 'took': float(hug_timer)}
    else:
        # No match - return a rejection.
        return {'success': False, 'api_key': True, 'error_message': 'Invalid project name! Pick from: "{}"'.format(supported_project_names), 'took': float(hug_timer)}
  else:
    # Invalid API key!
    return {'success': False, 'api_key': False, 'error_message': 'Invalid API key!', 'took': float(hug_timer)}
