#!/usr/bin/env python3
"""API server para sellado de archivos en una blockchain simulada."""

import argparse
import os
import re
from os import listdir
from hashlib import sha256
from web3 import Account, Web3
from web3.middleware import SignAndSendRawMiddlewareBuilder,ExtraDataToPOAMiddleware
from flask import Flask, current_app, json, jsonify, request, render_template_string
from eth_utils import is_hex, remove_0x_prefix
import yaml

app = Flask(__name__)

HASH_PATTERN = re.compile(r"0x[0-9a-fA-F]{64}$")


def is_valid_hash(string):
    """Valida que el string sea un hash SHA-256 en formato hexadecimal con prefijo '0x'."""
    return isinstance(string, str) and re.match(HASH_PATTERN, string)


class StamperException(Exception):
    """Excepción personalizada para errores relacionados con el proceso de sellado."""

def web3_connect(uri):
    if uri.startswith('http'):
        w3 = Web3(Web3.HTTPProvider(uri))
    else:
        w3 = Web3(Web3.IPCProvider(uri))
        
    if not w3.is_connected():
        raise ConnectionError(f"No se pudo conectar al nodo en: {uri}")
    
    return w3

def get_account_from_file(file_path, password):
    """
    Abre un archivo keystore específico, pide la contraseña 
    y devuelve el objeto Account.
    """
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No se encontró el archivo en la ruta: {file_path}")

    filename = os.path.basename(file_path)
    print(f"Desbloqueando cuenta desde: {filename}")

    with open(file_path, 'r') as f:
        keystore_contents = json.load(f)

    try:
        private_key = Account.decrypt(keystore_contents, password)
        return Account.from_key(private_key)
    except ValueError:
        raise ValueError("Contraseña incorrecta. El acceso fue denegado.")

def get_contract(w3, json_path):
    """
    Carga un contrato desde un archivo JSON basado en la red actual de w3.
    """
    
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"No se encontró el archivo: {json_path}")

    with open(json_path, 'r') as f:
        contract_data = json.load(f)

    
    network_id = str(w3.eth.chain_id)

    abi = contract_data.get('abi')
    networks = contract_data.get('networks', {})
    
    contract_info = networks.get(network_id)
    
    if not contract_info:
        print(f"El contrato {json_path} no está desplegado en la red con ID: {network_id} se usara la red 55555000000")
        contract_info = networks.get("55555000000")
        #raise ValueError(f"El contrato {json_path} no está desplegado en la red con ID: {network_id}")
    
    address = contract_info.get('address')

    print(f"Contrato '{contract_data['contractName']}' cargado en {address}")
    return w3.eth.contract(address=address, abi=abi)


# delete
class Stamper:
    """Clase que simula el proceso de sellado de archivos en una blockchain."""

    def __init__(self, address):
        self.block_number = 0
        self.database = {}
        self.address = address

    def stamp(self, hash_value):
        """Registra un hash en la "blockchain" simulada, incrementando el número de bloque."""
        self.block_number += 1
        if not is_valid_hash(hash_value):
            raise StamperException("Invalid hash format")
        if hash_value in self.database:
            raise StamperException("Hash is already stamped")
        self.database[hash_value] = {
            "signer": self.address,
            "blockNumber": self.block_number,
        }
        return sha256(
            f"{self.address}{self.block_number}{hash_value}".encode()
        ).hexdigest()

    def stamped(self, hash_value):
        """Devuelve la información de sellado para un hash dado, o None si no está sellado."""
        return self.database.get(hash_value)

def is_valid_signature(sig):
    """Valida que la firma tenga 65 bytes (130 caracteres hex + 0x)."""
    clean_sig = remove_0x_prefix(sig)
    return is_hex(clean_sig) and len(clean_sig) == 130

def setup_poa_middleware(w3):
    """Inyecta el middleware necesario para manejar cadenas de bloques con consenso PoA."""
    try:
        w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        print("Middleware de PoA inyectado correctamente.")
        return True
    except Exception as e:
        print(f"Error al inyectar middleware de PoA: {e}")
        return False
    
def setup_signing_middleware(w3, account):
    """
    Configura e inyecta el middleware de firmado automático 
    para una cuenta específica en la instancia de Web3.
    """
    try:
        signing_middleware = SignAndSendRawMiddlewareBuilder.build(account)
        
        w3.middleware_onion.inject(signing_middleware, layer=0)
        
        # set default account for transactions (optional, but can be useful for some libraries)
        w3.eth.default_account = account.address
        
        print(f"Middleware de firmado activado para: {account.address}")
        return True
        
    except Exception as e:
        print(f"Error al configurar el middleware: {e}")
        return False

@app.get("/stamped/<hash_value>")
def stamped(hash_value):
    """Endpoint para verificar si un hash ya ha sido sellado y obtener su información."""
    contract = current_app.config["contract"]
    
    if not is_valid_hash(hash_value):
        return jsonify(message="Invalid hash format"), 400
    
    try:
        result = contract.functions.stamped(hash_value).call()
        signer = result[0]
        block_number = result[1]
        if block_number == 0:
            return jsonify(message="Hash not found"), 404
        
        return jsonify({
            "signer": signer,
            "blockNumber": block_number
        }), 200

    except Exception as e:
        return jsonify(message=f"Internal error: {str(e)}"), 500


@app.post("/stamp")
def stamp():
    """Endpoint para sellar un hash, registrándolo en la "blockchain" simulada."""
    
    contract = current_app.config["contract"]
    w3 = current_app.config["w3"]
    
    if not request.is_json:
        return jsonify(message=f"Tipo de mensaje inválido: '{request.mimetype}'"), 400

    req = request.get_json(silent=True)
    
    if req is None:
        return jsonify(message="El cuerpo de la solicitud no es un JSON válido"), 400


    hash_value = req.get("hash")
    
    if not hash_value or not is_valid_hash(hash_value):
        return jsonify(message="Formato de hash inválido"), 400

    existing_data = contract.functions.stamped(hash_value).call()
    if existing_data[1] != 0: # blocknumber != 0 significa que ya está sellado
        return jsonify(
            message="Hash ya sellado",
            signer=existing_data[0],
            blockNumber=existing_data[1]
        ), 403

    signature = req.get("signature")
    
    try:
        if signature:
            if not is_valid_signature(signature):
                return jsonify(message="Formato de firma invalido"), 400
            
            hash_bytes = Web3.to_bytes(hexstr=hash_value)
            sig_bytes = Web3.to_bytes(hexstr=signature)
            
            tx_func = contract.functions.stampSigned(hash_bytes, sig_bytes)
        else:

            hash_bytes = Web3.to_bytes(hexstr=hash_value)
            tx_func = contract.functions.stamp(hash_bytes)
            
        account_address = w3.eth.default_account
        
        transaction_dict = tx_func.build_transaction({
            'from': account_address,
            'nonce': w3.eth.get_transaction_count(account_address),
            'gasPrice': w3.eth.gas_price,
        })

        
        tx_hash = w3.eth.send_transaction(transaction_dict)
               
        
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        return jsonify({
            "transaction": tx_hash.hex(),
            "blockNumber": receipt.blockNumber
        }), 201

    except Exception as e:
        return jsonify(message=f"Blockchain error: {str(e)}"), 400

@app.get("/openapi.json")
def get_openapi_json():
    """Devuelve el JSON solo si fue inyectado."""
    spec = current_app.config.get("openapi")
    if not spec:
        return jsonify(message="La especificación OpenAPI no está configurada"), 404
    return jsonify(spec)

@app.get("/swagger")
def swagger_ui():
    """Muestra la UI solo si existe la especificación."""
    if "openapi" not in current_app.config:
        return "Documentación no disponible", 404
        
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stamper API Docs</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
        <script>
            window.onload = () => {
                window.ui = SwaggerUIBundle({
                    url: '/openapi.json',
                    dom_id: '#swagger-ui',
                });
            };
        </script>
    </body>
    </html>
    """)


def create_app(keystore_dir,password,web3_uri, contract_json_path, openapi_path=None):
    """Función de fábrica para crear la aplicación Flask y configurar la instancia de Stamper."""
    w3 = web3_connect(web3_uri)
    contract = get_contract(w3, contract_json_path)
    keystore = [os.path.join(keystore_dir, f) for f in sorted(listdir(keystore_dir))]
    account = get_account_from_file(keystore[0], password)
    setup_poa_middleware(w3)
    setup_signing_middleware(w3, account)
    app.config["contract"] = contract
    app.config["w3"] = w3
    
    if openapi_path is not None:
        try:
            with open(openapi_path, 'r', encoding='utf-8') as f:
                app.config["openapi"] = yaml.safe_load(f)
        except Exception as e:
            print(f"Error al cargar OpenAPI desde {openapi_path}: {e}")
    
    return app

def read_password_from_file(file_path):
    """Lee la contraseña desde un archivo de texto plano."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"El archivo de contraseña no existe: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        password = f.readline().strip()
        
    if not password:
        raise ValueError(f"El archivo de contraseña está vacío: {file_path}")
        
    return password

if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Servidor API Stamper - Configuración de Seguridad"
    )

    group_password = parser.add_mutually_exclusive_group(required=True)
    
    group_password.add_argument(
        "-p", "--password", 
        type=str, 
        help="Contraseña de la cuenta Ethereum en texto plano."
    )
    
    group_password.add_argument(
        "-f", "--password-file", 
        type=str, 
        help="Ruta al archivo que contiene la contraseña."
    )

    args = parser.parse_args()
    
    if args.password_file:
        password = read_password_from_file(args.password_file)
    else:
        password = args.password
    keystore_dir = os.path.expanduser("~/.ethereum/keystore")
    web3_uri = os.path.expanduser("~/blockchain-iua/bfatest/node/geth.ipc")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
    
    openapi_path = os.path.join(root_dir, "openapi.yaml")
    contract_json_path = os.path.join(root_dir, "Stamper.json")
    
    create_app(keystore_dir, password, web3_uri, contract_json_path, openapi_path)
    app.run(debug=True)
