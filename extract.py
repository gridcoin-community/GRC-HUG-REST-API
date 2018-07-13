import gzip
import requests
import msgpack
from multiprocessing import Pool
import time
import xmltodict

WORKER_COUNT = 4 # Add CPUs & increase this value to supercharge processing downloaded

def extract_xml_step(xml_row):
    """
    Multiprocessing the extraction of key info from selected xml items!
    TODO: Handle varying XML format (different contents, validation, etc..)
    """
    return {'id': xml_row['id'], 'total_credit': xml_row['total_credit'], 'expavg_credit': xml_row['expavg_credit'], 'cpid': xml_row['cpid']}

def download_extract_stats(project_url):
    """
    Download an xml.gz, extract gz, parse xml, reduce & return data.
    """
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

        pool = Pool(processes=WORKER_COUNT) # 4 workers
        pool_xml_data = pool.map(extract_xml_step, file_content['users']['user']) # Deploy the pool workers
        msg_packed_results = msgpack.packb(pool_xml_data, use_bin_type=True)
        # unpacked_results = msgpack.unpackb(msg_packed_results, raw=False)
        return msg_packed_results
    else:
        print(downloaded_file.status_code)
        print("FAIL")
        # Didn't work
        return None

download_extract_stats("http://csgrid.org/csg/stats/user.gz")
