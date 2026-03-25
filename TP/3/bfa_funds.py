#!/usr/bin/env python3

import argparse
import getpass
import json
import os
import sys
from dotenv import load_dotenv
from web3 import Account, Web3


load_dotenv()

DEFAULT_WEB3_URI = "~/blockchain-iua/bfatest/node/geth.ipc"
KEYSTORE_PATH = os.getenv("KEYSTORE_PATH")
if not KEYSTORE_PATH or not os.path.isdir(KEYSTORE_PATH):
    print(f"No se encontró la carpeta de keystore en {KEYSTORE_PATH}", file=sys.stderr)
    sys.exit(1)

w3=None


def web3_connect(uri):
    """Conecta con un nodo Ethereum usando la URI dada.
    :param uri: La URI para la conexión
    Si la conexión falla se lanza una excepción.
    """
    global w3
    w3 = Web3(Web3.IPCProvider(uri))
    if not w3.is_connected():
        raise ConnectionError("Geth está apagado o la ruta es incorrecta.")
    

def get_private_key(src):
    """
    Pide la contraseña por consola (invisible) y busca la clave privada.
    """
    
    addr_target = checksum_address(src).lower()[2:]  # Quitamos el '0x' para buscar en los nombres de los archivos


    file = None
    for name in os.listdir(KEYSTORE_PATH):
        if addr_target in name.lower():
            file = os.path.join(KEYSTORE_PATH, name)
            break

    if not file:
        raise FileNotFoundError(f"No hay un archivo UTC para la cuenta {src}")


    password = getpass.getpass(f"Introduzca la contraseña para [{src}]: ")

    with open(file, 'r') as f:
        keystore_contents = json.load(f)

    try:
        private_key = Account.decrypt(keystore_contents, password)
        return private_key
    except ValueError:
        raise ValueError("Contraseña incorrecta. El acceso fue denegado.")

def checksum_address(addr):
    """Convierte una dirección a su formato checksum y la devuelve.
    Si la dirección no es válida, lanza una excepción.
    """
    try:
        return w3.to_checksum_address(addr)
    except ValueError:
        raise ValueError(f"La dirección '{addr}' no es válida.")

def balance(account, unit):
    """Imprime el balance de una cuenta

    :param account: La dirección de la cuenta
    :param unit: Las unidades en las que se desea el resultado. (wei, Kwei, Mwei, Gwei, microether, milliether, ether)
    """
    valid_addr = checksum_address(account)
    wei_balance = w3.eth.get_balance(valid_addr)
    unit_balance = w3.from_wei(wei_balance, unit)
    print(f"Balance de {account}: {unit_balance} {unit}")

def transfer(src, dst, amount, unit):
    """Transfiere ether de una cuenta a otra.

    :param src: La dirección de la cuenta de origen.
    :param dst: La dirección de la cuenta de destino.
    :param amount: Monto que se desea transferir.
    :param unit: Unidades en las que está expresado el monto.
    Si la transacción es exitosa, imprime "Transferencia exitosa".
    Si la transacción falla, termina el programa con error e indica la causa.
    """
    src_addr = checksum_address(src)
    dst_addr = checksum_address(dst)
    
    amount_wei = w3.to_wei(amount, unit)
    if w3.eth.get_balance(src_addr) < amount_wei:
        raise ValueError("Saldo insuficiente para realizar la transferencia.")
    
    private_key = get_private_key(src_addr)
    
    print(f"Preparando envío de {amount} {unit}...")
    nonce = w3.eth.get_transaction_count(src_addr)
        
    tx = {
            'nonce': nonce,
            'to': dst_addr,
            'value': amount_wei,
            'gas': 21000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id # Detecta automáticamente si es BFA o Mainnet
        }

        
    signed_tx = Account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
    print(f"Transacción enviada a la red. Hash: {tx_hash.hex()}")
    print("Esperando confirmación (esto puede tardar unos segundos)...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt['status'] == 1:
            print(f"Transferencia exitosa!")
            print(f"Hash: {tx_hash.hex()}")
            print(f"Bloque: {receipt['blockNumber']}")
    else:
            print(f"Error: La transacción fue REVERTIDA por la red.")
            print(f"Hash: {tx_hash.hex()}")
    

def accounts():
    """Lista las cuentas asociadas con un nodo"""
    print(f"\n{'DIRECCIÓN':<45} | {'SALDO (ETH)':<15}")
    print("-" * 65)
    
    found_files = 0
    
    for file in os.listdir(KEYSTORE_PATH):
        # El estándar de Geth: UTC--fecha--direccion
        if "--" in file:
            try:
                address_raw = "0x" + file.split("--")[-1]
                address = checksum_address(address_raw)
        
                balance_wei = w3.eth.get_balance(address)
                balance_eth = w3.from_wei(balance_wei, 'ether')
                
                print(f"{address:<45} | {balance_eth:>12.6f} ETH")
                
                found_files += 1
                
            except Exception:
                continue

    if found_files == 0:
        print("No se encontraron archivos de cuentas validas en el keystore.")
    print("-" * 65 + "\n")

def address(x):
    """Verifica si su argumento tiene forma de dirección ethereum válida"""
    
    if x[:2] == '0x' or x[:2] == '0X':
        try:
            b = bytes.fromhex(x[2:])
            if len(b) == 20:
                return x
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Invalid address: '{x}'")                                                                                                                                               



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=
        f"""Maneja los fondos de una cuenta en una red ethereum.
        Permite consultar el balance y realizar transferencias. Por defecto, intenta conectarse mediante '{DEFAULT_WEB3_URI}'""")
    parser.add_argument("--uri", help="URI para la conexión con geth",default=DEFAULT_WEB3_URI)
    subparsers = parser.add_subparsers(title="command", dest="command")
    subparsers.required=True
    parser_balance = subparsers.add_parser("balance", help="Obtiene el balance de una cuenta")
    parser_balance.add_argument("--unit", help="Unidades en las que está expresado el monto", choices=['wei', 'Kwei', 'Mwei', 'Gwei', 'microether', 'milliether','ether'], default='wei')
    parser_balance.add_argument("--account", "-a", help="Cuenta de la que se quiere obtener el balance", type=address, required=True)
    parser_transfer = subparsers.add_parser("transfer", help="Transfiere fondos de una cuenta a otra")
    parser_transfer.add_argument("--from", help="Cuenta de origen", type=address, required=True, dest='src')
    parser_transfer.add_argument("--to", help="Cuenta de destino", type=address, required=True, dest='dst')
    parser_transfer.add_argument("--amount", help="Monto a transferir", type=int, required=True)
    parser_transfer.add_argument("--unit", help="Unidades en las que está expresado el monto", choices=['wei', 'Kwei', 'Mwei', 'Gwei', 'microether', 'milliether','ether'], default='wei')
    parser_accounts = subparsers.add_parser("accounts", help="Lista las cuentas de un nodo")
    args = parser.parse_args()
    # La URI elegida por el usuario está disponible como args.uri
    # Lo que sigue probablemente debería estar encerrado en un bloque try: ... except:
    
    try:
        web3_connect(args.uri)
        if args.command == "balance":
            balance(args.account, args.unit)
        elif args.command == "transfer":
            transfer(args.src, args.dst, args.amount, args.unit)
        elif args.command == "accounts":
            accounts()
        else:
            print(f"Comando desconocido: {args.command}", file=sys.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    