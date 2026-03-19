import requests

def java_next_int(seed):
    seed = (seed * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
    res = seed >> 16
    if res >= 2**31: # Convertir a entero de 32 bits con signo
        res -= 2**32
    return seed, res

def get_seed(n1, n2):
    bseed = (n1 & 0xFFFFFFFF) << 16
    for i in range(2**16):
        seed = bseed | i
        next_s, val = java_next_int(seed)
        
        if val == n2:
            return next_s
    return None


server = "https://cripto.iua.edu.ar/blockchain"
email = "bvargas161@alumnos.iua.edu.ar"

print("Java Integer Predictor:")

response =  requests.get(f"{server}/javarand/{email}/challenge")
n1 = int(response.text)
print(f"First value: {n1}")

response =  requests.get(f"{server}/javarand/{email}/challenge")
n2 = int(response.text)
print(f"Second value: {n2}")

seed = get_seed(n1, n2)

if seed is not None:
    next_seed, next_val = java_next_int(seed)
    print(f"Predicted seed: {seed}")
    print(f"Next value predicted: {next_val}")
    
    
    response = requests.post(
    f"{server}/javarand/{email}/answer",
    files = { "number": str(next_val).encode('ascii')})
    
    print(f"Status code: {response.status_code}")
    print(response.text)
    
else:
    print("Seed not found.")