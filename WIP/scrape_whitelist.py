from bs4 import BeautifulSoup

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
