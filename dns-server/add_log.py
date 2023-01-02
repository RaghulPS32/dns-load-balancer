import requests

f = open("top_domains.txt")
for url in f:
	try:
		print("Trying: ",url)
		print(requests.get("https://"+url),timeout=15)
	except Exception:
		print("Could'nt Get: ",url)
