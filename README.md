# Repositorio personal — Blockchain y Contratos Inteligentes, IUA 2026

## Presentación

Este repositorio contiene las resoluciones de trabajos prácticos de la materia, organizados por carpeta según la guía de cursado.

## Datos del alumno

- **Nombre:** Vargas Benjamin
- **Email institucional:** bvargas161@alumnos.iua.edu.ar

## Estructura del repositorio

```text
ByCI/
├── README.md
└── TP/
    ├── 1/
    │   ├── collision_finder.py
    │   ├── PoW.py
    │   ├── README.md
    │   └── requirements.txt
    ├── 2/
    │   ├── dsa_pkey_finder.py
    │   ├── java_integer_predictor.py
    │   ├── README.md
    │   └── requirements.txt
    ├── 3/
    │   ├── bfa_funds.py
    │   ├── show_transactions.py
    │   ├── README.md
    │   └── requirements.txt
    ├── 4/
    │   ├── Stamper.json
    │   ├── openapi.yaml
    │   ├── api/python/
    │   │   ├── apiserver.py
    │   │   ├── test_apiserver.py
    │   │   ├── README.md
    │   │   └── requirements.txt
    │   ├── app web/
    │   │   ├── index.html
    │   │   ├── app.js
    │   │   ├── style.css
    │   │   └── README.md
    │   └── README.md
    └── 5/
        ├── README.md
        └── Ballot/
            ├── contracts/Ballot.sol
            ├── scripts/deploy.js
            ├── test/ballot.test.js
            ├── hardhat.config.js
            └── package.json
```

## Resumen por trabajo práctico

- **TP 1 — Hashes y PoW**
	- Búsqueda de colisiones SHA-256 truncado.
	- Resolución de prueba de trabajo sobre blockchain ficticia.

- **TP 2 — Vulnerabilidades criptográficas**
	- Predicción del PRNG de Java (`java.util.Random`).
	- Recuperación de clave privada DSA por reutilización de nonce `k`.

- **TP 3 — Red BFA y análisis de transacciones**
	- Scripts para consultar balances, cuentas y transferencias firmadas.
	- Exploración de transacciones por rango de bloques.

- **TP 4 — Servicio de sellado con contrato inteligente**
	- API REST en Python/Flask para registrar y consultar hashes en contrato.
	- Especificación OpenAPI.
	- Cliente web estático para hashear archivos y consumir la API.

- **TP 5 — Smart contract de votación (Hardhat + Solidity)**
	- Contrato `Ballot.sol`.
	- Script de despliegue.
	- Tests unitarios con Hardhat.

## Notas

- Cada TP incluye su propio `README.md` con detalle técnico y comandos de ejecución.

