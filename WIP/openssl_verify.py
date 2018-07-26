from OpenSSL import crypto
import xmltodict
import sys

def get_pub_key(filename):
    """Return the pub key"""
    try:
        with open(filename) as project_pub_key:
            return project_pub_key
    except IOError:
        print("File not found: "+filename)
        return None

def get_produced_xml(filename):
    """Return the project produced XML as JSON"""
    try:
        with open(filename) as project_produced_xml:
            xml_to_dict = xmltodict.parse(project_produced_xml)
            return xml_to_dict
    except IOError:
        print("File not found: "+filename)
        return None

def verify_signature(pubkey, message, signature):
      """Verifies a message against a signature."""
      try:
        crypto.verify(pubkey, signature, message, 'sha512')
        return True
      except:
        return False

retrieved_pub_key = get_pub_key('/home/derp/Desktop/BOINC WORKSHOP/external_system_key_public.pem')
project_produced_dict = get_produced_xml('/home/derp/Desktop/BOINC WORKSHOP/signature.xml')

print(retrieved_pub_key)
print("-----------")
print(project_produced_dict)
print("===========")
print(verify_signature(retrieved_pub_key, project_produced_dict['msg'], project_produced_dict['signature']))
