import webbrowser as wb
import urllib.parse as parse

url = "http://localhost:5001/images?" +  parse.urlencode({"ids":"1 2 3 4", "query":"Cats"})
print(url)
wb.open_new(url)