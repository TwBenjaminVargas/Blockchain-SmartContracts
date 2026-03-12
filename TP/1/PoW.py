import requests
from datetime import datetime
import base64
from hashlib import sha256
from itertools import count

server = "https://cripto.iua.edu.ar/blockchain"

def create_block(prevblock,timestamp,email):
    new_block_number = int.from_bytes(prevblock[0:8], "big") + 1
    new_timestamp = int(timestamp)
    new_target = prevblock[16:24]
    previous_block_hash = sha256(prevblock).digest()
    email_hash = sha256(email.encode("utf-8")).digest()
    
    new_block = bytearray(96)
    new_block[0:8] = new_block_number.to_bytes(8, "big")
    new_block[8:16] = new_timestamp.to_bytes(8, "big")
    new_block[16:24] = new_target
    new_block[24:32] = (0).to_bytes(8, "big")
    new_block[32:64] = previous_block_hash
    new_block[64:96] = email_hash
    return new_block

def print_block(block):
    print(f"SHA256: {sha256(block).hexdigest()}")
    block_number = int.from_bytes(block[:8], "big")
    print(f"Block number: {block_number}")
    timestamp = int.from_bytes(block[8:16], "big")
    date_and_time = datetime.fromtimestamp(timestamp)
    print(f"Date: {date_and_time}")
    msb_64_target = int.from_bytes(block[16:24], "big")
    target = msb_64_target << 192
    print(f"Target: {target:064x}")
    lnonce = int.from_bytes(block[24:32], "big")
    print(f"Nonce: {lnonce}")
    previous_block_hash = block[32:64]
    print(f"Previous Block Hash: {previous_block_hash.hex()}")
    email_hash = block[64:96]
    print(f"Email Hash: {email_hash.hex()}\n")

def upload_block(block, email):
    encoded_block = base64.b64encode(block)
    response = requests.post(
        f"{server}/pow/{email}/blocks",
        files = {"block": encoded_block })
    return response
    
print("Proof of Work:")
EMAIL = input("Enter your email: ")

print("\nFetching latest block...")
response = requests.get(f"{server}/pow/{EMAIL}/blocks/latest")

if response.status_code != 200:
    print("Error fetching latest block:", response.status_code)
    exit(1)

block = base64.b64decode(response.content)
msb_64_target = int.from_bytes(block[16:24], "big")
target = msb_64_target << 192

print("\nLatest block data:\n")
print_block(block)

print("Finding valid nonce...")

controltime = start_time = datetime.now()
new_block = create_block(block, start_time.timestamp(), EMAIL)

nonce=1
while True:
    new_block[24:32] = nonce.to_bytes(8, "big")
    block_hash = sha256(new_block).digest()
    if int.from_bytes(block_hash, "big") < target:
        break
    if(datetime.now() - controltime).total_seconds() > 30:
        print("Timeout reached, fixing block timestamp")
        new_block[8:16] = int(datetime.now().timestamp()).to_bytes(8, "big")
        nonce = 1
        controltime = datetime.now()
    nonce += 1

end_time = datetime.now()
print("\nValid nonce found!\n")
print_block(new_block)
print(f"Time taken: {(end_time - start_time).total_seconds():.2f} seconds")

print("Submitting new block to server...")    
response = upload_block(new_block, EMAIL)
if response.status_code == 200:
    print("Block submitted successfully!")
    print(response.text)
else:
    print("Error submitting block:", response.status_code)
    print(response.text)