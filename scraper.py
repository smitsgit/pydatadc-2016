import elasticsearch
import requests, json, datetime, time, re
from bs4 import BeautifulSoup

requests.packages.urllib3.disable_warnings()

# Configurations
sites = ['http://marshyski.com', 'http://marshyski.com/man-behind-the-keyboard',
        'http://marshyski.com/music', 'http://www.npr.org/sections/news/', 'https://news.google.com/']

index_name = "websites"
index_type = "sites"
elastic_host = "127.0.0.1"
elastic_port = "9200"

# Connect to ElasticSearch
es = elasticsearch.Elasticsearch(elastic_host, port=elastic_port)

# Delete & Create index
es.indices.delete(index=index_name, ignore=[400, 404])
es.indices.create(index=index_name, ignore=400)

# Make requests in configuration
for URL in sites:

    try:
       r = requests.get(URL, verify=False)
       r_text = r.text
       soup = BeautifulSoup(r_text, "lxml")
       title = soup.title.string
       if r.status_code == 200:

          # Get only text from request body
          site_text = soup.get_text()

          # Strip HTML and join new lines
          lines = (line.strip() for line in site_text.splitlines())
          chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
          join = ' '.join(chunk for chunk in chunks if chunk)
          text = re.sub(r'[^a-zA-Z\d\s]', '', join)

          for script in soup(["script", "style", "title", "a", "footer"]) + \
                        soup.findAll('div', attrs={'class': 'footer'}) + \
                        soup.findAll('div', attrs={'id': 'sidebar'}):
                        script.extract()

          site_text = soup.get_text().replace('"', "'")

          lines = (line.strip() for line in site_text.splitlines())
          chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
          text = ' '.join(chunk for chunk in chunks if chunk)

	  date_time = datetime.datetime.strftime(datetime.datetime.now(), '%Y%m%d%H%M%S')

          # Build request to ElasticSearch
          js = {"title":title, "url":URL, "date":date_time, "body":text}
          data = json.dumps(js)

          print data

          # POST to ElasticSearch
          res = es.index(index=index_name, doc_type=index_type, id=date_time, body=data)
          print "Created", res['created'], "\n"
          time.sleep(1.0)

       else:

          print URL, r.status_code, "[FAIL]"

    except:
          print URL, "[FAIL]"
