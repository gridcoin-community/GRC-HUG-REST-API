import requests
from bs4 import BeautifulSoup

def scrape_gridcoinstats_for_whitelist():
	"""
	A function to scrape gridcoinstats.eu for the active whitelist.
	"""
	scraped_page = requests.get("https://gridcoinstats.eu/project")
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


"""
['http://yafu.myfirewall.org/yafu', 'https://boinc.multi-pool.info/latinsquares', 'http://srbase.my-firewall.org/sr5', 'https://www.gpugrid.net', 'http://gene.disi.unitn.it/test/', 'https://escatter11.fullerton.edu/nfs', 'http://23.253.170.196', 'http://setiathome.ssl.berkeley.edu', 'http://www.rechenkraft.net/yoyo', 'http://www.enigmaathome.net', 'http://boinc.bakerlab.org/rosetta', 'http://milkyway.cs.rpi.edu/milkyway', 'https://universeathome.pl/universe', 'http://asteroidsathome.net/boinc', 'https://cosmologyathome.org', 'https://sech.me/boinc/Amicable', 'https://lhcathome.cern.ch/lhcathome', 'https://numberfields.asu.edu/NumberFields', 'https://boinc.vgtu.lt', 'https://boinc.thesonntags.com/collatz', 'https://csgrid.org/csg']
"""
