import base64
import requests
import hashlib


import requests


def get_pkey(q, r, s1, s2, msg1, msg2):
    h1 = int(hashlib.sha256(msg1.encode()).hexdigest(), 16)
    h2 = int(hashlib.sha256(msg2.encode()).hexdigest(), 16)
    den_k = (s1 - s2) % q
    inv_den_k = pow(den_k, -1, q)
    k = ((h1 - h2) * inv_den_k) % q
    inv_r = pow(r, -1, q)
    x = (inv_r * (k * s1 - h1)) % q
    return x


server = "https://cripto.iua.edu.ar/blockchain"
email = "bvargas161@alumnos.iua.edu.ar"


print("DSA private key finder:\n")

q = 0
try:
    response = requests.get(f"{server}/dsa/{email}/public-key")
    if response.status_code == 200:
        params = response.json()
        q = int(params['Q'])
    else:
        print(f"Error fetching DSA public-key: {response.status_code}")
        exit(1)
except Exception as e:
    print(f"Connection error: {e}")
    exit(1)
    
signs = {}

i = 0
pkey = 0
print("Looking for colision 'r' values...")
while True:
    i += 1
    
    text_msg = f"m_{i}"
    msg_b64 = base64.b64encode(text_msg.encode()).decode()

    try:
        response = requests.post(
            f"{server}/dsa/{email}/sign",
            files={"message": msg_b64}
        )
        
        if response.status_code == 200:
            data = response.json()
            r = int(data['r'])
            s = int(data['s'])

            if r in signs:
                prev_s, prev_msg = signs[r]
                
                print(f"\nColision detected!\n")
                print(f"r: {r}")
                print(f"msg1: {prev_msg} -> s1: {prev_s}")
                print(f"msg 2: {text_msg} -> s2: {s}")
                
                # Aquí llamarías a tu función para calcular la X
                pkey = get_pkey(q, r, prev_s, s, prev_msg, text_msg)
                break
            else:
                signs[r] = (s, text_msg)
        else:
            print(f"Server Error: {response.status_code}")
            exit(1)

    except Exception as e:
        print(f"Connection error: {e}")
        exit(1)

print(f"\nPrivate key found: {pkey}\n")

response = requests.post(
    f"{server}/dsa/{email}/answer",
    files = { "private-key": str(pkey)})

print(f"Status code: {response.status_code}")
print(response.text)