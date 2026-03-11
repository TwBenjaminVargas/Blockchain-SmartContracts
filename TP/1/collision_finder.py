from hashlib import sha256
from time import time
import requests

server = "https://cripto.iua.edu.ar/blockchain"

print("Collision finder SHA-256-48:")
EMAIL = input("Enter your email: ")


start_time = time()


seen = {}
msg1= ""
msg2= ""
h = ""
i=0
while True:
    msg1 = EMAIL + str(i)
    h= sha256(msg1.encode()).hexdigest()[:12]
    if h in seen:
        msg2 = seen[h]
        break
    seen[h] = msg1
    i += 1
        
end_time = time()

print(f"Found collision: \"{seen[h]}\"")
print("msg1:", msg1)
print("msg2:", msg2)
print(f"Search time: {end_time - start_time:.2f} seconds")


print("Submitting collision to server...")
response = requests.post(
    f"{server}/collision/{EMAIL}/answer", 
    files={"message1": msg1.encode(), "message2": msg2.encode()})
print(response.status_code)
print(response.text)