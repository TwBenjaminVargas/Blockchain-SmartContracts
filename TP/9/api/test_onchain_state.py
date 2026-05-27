# pylint: disable=missing-function-docstring
"""
Tests que verifican que la API refleja cambios de estado realizados directamente
on-chain, sin pasar por los endpoints de escritura de la API.

Principio de diseño: todas las operaciones de escritura del owner sobre el contrato
se realizan directamente on-chain (send_authorize_tx / send_unauthorize_tx), sin pasar
nunca por la API. Así el NonceManager del servidor no interviene y la compensación del
nonce al final del módulo es exactamente predecible (current - 2).
"""

import time

import pytest
import requests
from eth_account import Account
from jsonschema import validate
from web3.types import RPCEndpoint

from test_apiserver import (
    authorized_schema,
    fund_account,
    get_contract_address,
    get_factory_contract,
    get_w3,
    make_register_message,
    post_register,
    send_register_tx,
    sign_bytes,
    url,
    wait_for_registration_status,
)


@pytest.fixture(scope="module", autouse=True)
def sync_owner_nonce_after_direct_writes():
    """Compensa las transacciones directas del owner (sin pasar por la API)
    ajustando el nonce on-chain al final del módulo.

    Permite que test_apiserver.py funcione correctamente después de este módulo
    en implementaciones que cachean el nonce del owner (ej. ethers v6 NonceManager).
    send_authorize_tx y send_unauthorize_tx envían 2 txs del owner directamente
    on-chain; revertir el nonce 2 unidades sincroniza la cadena con lo que el
    servidor espera.
    """
    yield
    w3 = get_w3()
    _, owner = get_factory_contract()
    current = w3.eth.get_transaction_count(owner.address)
    w3.provider.make_request(RPCEndpoint("hardhat_setNonce"), [owner.address, hex(current - 2)])


@pytest.fixture(autouse=True)
def mine_after_test():
    yield
    get_w3().provider.make_request(RPCEndpoint("evm_mine"), [])


def _send_owner_tx(fn) -> None:
    """Construye, firma y envía una transacción del owner para la función de contrato dada."""
    w3 = get_w3()
    _, owner = get_factory_contract()
    estimated_gas = fn.estimate_gas({"from": owner.address})
    tx = fn.build_transaction(
        {
            "from": owner.address,
            "nonce": w3.eth.get_transaction_count(owner.address),
            "gas": int(estimated_gas * 1.3),
            "gasPrice": w3.to_wei("1", "gwei"),
        }
    )
    signed = owner.sign_transaction(tx)  # type: ignore[arg-type]
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    w3.eth.wait_for_transaction_receipt(tx_hash)


def send_authorize_tx(address: str) -> None:
    """Llama a factory.authorize(address) directamente desde el owner, sin pasar por la API."""
    factory, _ = get_factory_contract()
    _send_owner_tx(factory.functions.authorize(address))


def send_unauthorize_tx(address: str) -> None:
    """Llama a factory.unauthorize(address) directamente desde el owner, sin pasar por la API."""
    factory, _ = get_factory_contract()
    _send_owner_tx(factory.functions.unauthorize(address))


def test_authorized_reflects_onchain_unauthorization() -> None:
    """authorize directo on-chain → unauthorize directo on-chain → GET /authorized debe ser false.

    Detecta implementaciones que leen el estado de autorización solo de la DB interna
    en lugar de reflejar cambios on-chain que no pasaron por la API.

    Flujo:
      1. Registrar vía API (el owner no envía txs en este paso).
      2. Autorizar directamente on-chain (sin pasar por la API).
      3. Desautorizar directamente on-chain (sin pasar por la API).
      4. Verificar que /authorized devuelve false (solo lecturas de aquí en adelante).
    """
    contract_address = get_contract_address()

    account = Account().create()
    fund_account(account.address)
    send_register_tx(account)
    msg = make_register_message(contract_address, "Onchain Unauth Test")
    response = post_register(account.address, sign_bytes(msg, account), "Onchain Unauth Test")
    assert response.status_code == 200
    assert wait_for_registration_status(account.address, "registered"), \
        "La cuenta no llegó a estado 'registered'"

    # Ambas operaciones del owner son directas: el NonceManager del servidor no interviene.
    send_authorize_tx(account.address)
    assert wait_for_registration_status(account.address, "authorized"), \
        "La cuenta no llegó a estado 'authorized'"

    send_unauthorize_tx(account.address)

    # Esperar a que el event listener procese CreatorUnauthorized.
    deadline = time.time() + 15
    while time.time() < deadline:
        get_w3().provider.make_request(RPCEndpoint("evm_mine"), [])
        response = requests.get(url("authorized", account.address), timeout=3)
        if response.status_code == 200 and response.json().get("authorized") is False:
            break
        time.sleep(0.5)
    else:
        pytest.fail("/authorized no detectó la desautorización on-chain directa")

    validate(instance=response.json(), schema=authorized_schema)
    assert response.json()["authorized"] is False, \
        "/authorized no detectó la desautorización realizada directamente on-chain"
