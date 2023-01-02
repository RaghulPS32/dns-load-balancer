import requests as req
import requests.exceptions
import ast
import time
import matplotlib.pyplot as plt
import numpy as np
from threading import Thread
import random as rn



log = open("log.json","r")
cont = log.read()
log.close()
cont = ast.literal_eval(cont)
cont = list(cont.keys())
count = 0

def do_request(url):
	global count
	try:
		req.get(url, timeout=3)
		count += 1
		
	except requests.exceptions.ConnectTimeout:
		return
	except:
		count += 1

threads = []
for i in range(len(cont)):
	#th = Thread(target=do_request, args=("http://"+cont[rn.randint(0,len(cont)-1)],))
	th = Thread(target=do_request, args=("http://"+cont[i],))
	th.start()
	threads.append(th)

print("started process... waiting for them")
[i.join() for i in threads]
labels = ['resolved','unresolved']
y = np.array([count/len(cont) * 100,100-(count/len(cont) * 100)])
plt.pie(y,autopct='%1.1f%%',startangle=90)
plt.axis('equal')
plt.legend( loc = 'lower right', labels=labels)
print(f"{count/len(cont) * 100 : .2f}% success rate")
print(f"{100 - (count/len(cont) * 100) : .2f}% failure rate")
plt.show()
print("Done!")
