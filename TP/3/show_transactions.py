#!/usr/bin/env python3
"""Este programa muestra las transacciones ocurridas en un determinado rango de bloques,
eventualmente restringidas a las que corresponden a una o más direcciones.
Sólo deben considerarse las transacciones que implican transferencia de ether.
Los bloques analizados son todos aquellos comprendidos entre los argumentos first-block
y last-block, ambos incluidos.
Si se omite first-block, se comienza en el bloque 0.
Si se omite last-block, se continúa hasta el último bloque.
Se pueden especificar una o más direcciones para restringir la búsqueda a las transacciones
en las que dichas direcciones son origen o destino.
Si se especifica la opción add, cada vez que se encuentra una transacción que responde a
los criterios de búsqueda, se agregan las cuentas intervinientes a la lista de direcciones
a reportar.
La opción "--short" trunca las direcciones a los 8 primeros caracteres.
La salida debe producirse en al menos los dos formatos siguientes:
'plain': <origen> -> <destino>: <monto> (bloque)
'graphviz': Debe producir un grafo representable por graphviz. Ejemplo (con opcion --short)
digraph Transfers {
"8ffD013B" -> "9F4BA634" [label="1 Gwei (1194114)"]
"8ffD013B" -> "9F4BA634" [label="1 ether (1194207)"]
"9F4BA634" -> "8ffD013B" [label="1 wei (1194216)"]
"8ffD013B" -> "46e2a9e9" [label="2000 ether (1195554)"]
"8ffD013B" -> "8042435B" [label="1000 ether (1195572)"]
"8042435B" -> "8ffD013B" [label="1 ether (1195584)"]
"8ffD013B" -> "55C37a7E" [label="1000 ether (1195623)"]
"8ffD013B" -> "fD52f36a" [label="1000 ether (1195644)"]
}
"""
import argparse
from web3 import Web3
import sys
from web3.middleware import ExtraDataToPOAMiddleware
import graphviz

DEFAULT_WEB3_URI = "~/blockchain-iua/bfatest/node/geth.ipc"
ONE_ETHER_WEI = None

w3 = None


def web3_connect(uri):
    """Conecta con un nodo Ethereum usando la URI dada.
    :param uri: La URI para la conexión
    Si la conexión falla se lanza una excepción.
    """
    global w3
    w3 = Web3(Web3.IPCProvider(uri))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    if not w3.is_connected():
        raise ConnectionError("Geth está apagado o la ruta es incorrecta.")

def checksum_address(addr):
    """Convierte una dirección a su formato checksum y la devuelve.
    Si la dirección no es válida, lanza una excepción.
    """
    try:
        return w3.to_checksum_address(addr)
    except ValueError:
        raise ValueError(f"La dirección '{addr}' no es válida.")

def checksum_addresses(addrs):
    """Convierte una lista de direcciones a su formato checksum y las devuelve.
    Si alguna dirección no es válida, lanza una excepción.
    """
    return [checksum_address(addr) for addr in addrs]


def history(start_block, end_block):
    transactions = []
    for i in range(start_block, end_block + 1):
        try:
            block = w3.eth.get_block(i, full_transactions=True) 
            for tx in block.transactions:
                if tx['value'] >= ONE_ETHER_WEI:
                    transactions.append(tx)                    
        except Exception:
            continue
    return transactions

def history_by_address(targets, start_block, end_block):
    transactions = []
    for i in range(start_block, end_block + 1):
        try:
            block = w3.eth.get_block(i, full_transactions=True) 
            for tx in block.transactions:
                if tx['value'] >= ONE_ETHER_WEI and (tx['from'] in targets or tx['to'] in targets):
                    transactions.append(tx)                    
        except Exception:
            continue
    return transactions

def history_by_address_add(targets, start_block, end_block):
    transactions = []
    for i in range(start_block, end_block + 1):
        try:
            block = w3.eth.get_block(i, full_transactions=True) 
            for tx in block.transactions:
                if tx['value'] >= ONE_ETHER_WEI and (tx['from'] in targets or tx['to'] in targets):
                    transactions.append(tx)
                    if tx['from'] not in targets:
                        targets.append(tx['from'])
                    if tx['to'] not in targets:
                        targets.append(tx['to'])
        except Exception:
            continue
    return transactions

def format_graphviz(transactions, short=False):
    
    if not transactions:
        return None

    dot = graphviz.Digraph('Transfers', comment='Blockchain Transactions')
    dot.attr(rankdir='LR', size='10,10')
    

    dot.attr('node', shape='box', style='rounded,filled', 
             fillcolor='#E8F0FE', fontname='Arial', color='#1A73E8')
    
    dot.attr('edge', fontname='Verdana', fontsize='10', color='#5F6368')
    for tx in transactions:
        
        orig = tx['from']
        dest = tx['to']
        
        if short:
            orig_label = orig[2:10]
            dest_label = dest[2:10]
        else:
            orig_label = orig
            dest_label = dest

        label_amount = f"{Web3.from_wei(tx['value'], 'ether')} ether"

        edge_label = f"{label_amount}\n(Block: {tx['blockNumber']})"
        
        dot.edge(orig_label, dest_label, label=edge_label)

    return dot

def format_plain(transactions, short=False):
    if not transactions:
        return "No se encontraron transacciones relevantes."

    lines = []
    for tx in transactions:
        orig = tx['from']
        dest = tx['to']
        
        if short:
            orig_str = orig[2:10]
            dest_str = dest[2:10]
    
        else:
            orig_str = orig
            dest_str = dest


        amount = f"{Web3.from_wei(tx['value'], 'ether')} ether"
    
        
        line = f"{orig_str} -> {dest_str}: {amount} ({tx['blockNumber']})"
        lines.append(line)

    return "\n".join(lines)

def address(x):
    """Verifica si su argumento tiene forma de dirección ethereum válida"""

    if x[:2] == "0x" or x[:2] == "0X":
        try:
            b = bytes.fromhex(x[2:])
            if len(b) == 20:
                return x
        except ValueError:
            pass
    raise argparse.ArgumentTypeError(f"Invalid address: '{x}'")


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "addresses",
        metavar="ADDRESS",
        type=address,
        nargs="*",
        help="Direcciones a buscar",
    )
    parser.add_argument(
        "--add",
        help="Agrega las direcciones encontradas a la búsqueda",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--first-block",
        "-f",
        help="Primer bloque del rango en el cual buscar",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--last-block",
        "-l",
        help="Último bloque del rango en el cual buscar",
        #type=int,
        default="latest",
    )
    parser.add_argument(
        "--format",
        help="Formato de salida",
        choices=["plain", "graphviz"],
        default="plain",
    )
    parser.add_argument(
        "--short",
        help="Trunca las direcciones a los 8 primeros caracteres",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--uri", help="URI para la conexión con geth", default=DEFAULT_WEB3_URI
    )
    args = parser.parse_args()
    
    try:
        web3_connect(args.uri)
        ONE_ETHER_WEI = w3.to_wei(1, 'ether') # limite para considerar una transacción como relevante
        transactions = []
        
        last_block = int(args.last_block) if args.last_block != "latest" else w3.eth.block_number
        
        if args.addresses:
            args.addresses = checksum_addresses(args.addresses)
            if args.add:
                transactions = history_by_address_add(args.addresses, args.first_block, last_block)
            else:
                transactions = history_by_address(args.addresses, args.first_block, last_block)
        else:
             transactions = history(args.first_block, last_block)
             
        if args.format == "plain":
            output = format_plain(transactions, args.short)
        if args.format == "graphviz":
            output = format_graphviz(transactions, args.short).source
        
        print(output)
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
