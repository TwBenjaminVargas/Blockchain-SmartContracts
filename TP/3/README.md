# TP 3 - Red BFA y Scripts de Analisis

## Consigna

En este trabajo practico se realizaron dos partes principales:

1. **Ejecucion de una transaccion en la red de prueba BFA** (punto 3).
2. **Implementacion de scripts en Python para gestion y analisis de transacciones** (punto 4).

Como requisito previo, la cuenta utilizada para operar fue creada y resguardada correctamente en el **punto 2** de la consigna, conservando su archivo de keystore y contraseña.

## Estructura de la solucion

- `bfa_funds.py`: consultas de balance, listado de cuentas y transferencia firmada desde keystore.
- `show_transactions.py`: recorrido de bloques, filtrado de transferencias de ether y salida en formato plain o graphviz.

---

## 3) Realizar una transaccion

### Objetivo

Enviar **1 wei** a la direccion indicada por la consigna (`0x5A5a966FeAA14e3018561314AA922f8e3A1E890d`) y verificar el impacto en el balance final.

### Procedimiento realizado

El proceso se inicia con una auditoria del estado actual de la cuenta principal del nodo. Se utiliza el comando `eth.getBalance` para extraer el saldo bruto en la unidad minima del protocolo (Wei). Posteriormente, se aplica el metodo `web3.fromWei` para normalizar la lectura a una escala humana. Se confirma un saldo inicial de **0.0001 ETH**, validando que la consola de JavaScript esta correctamente sincronizada y operativa para transaccionar.

![Auditoria de saldo inicial](https://drive.google.com/drive/folders/12YvXn2_2DJ1SvTjsv5siBEDNLpq9WJQb)

Luego se procede a la ejecucion del requerimiento tecnico. Para garantizar la precision y evitar errores de direccionamiento, se definen variables de entorno para la cuenta de origen (`miCuenta`) y la direccion de destino especificada en la consigna (`destino_p3`).

Se emite la transaccion mediante el metodo `eth.sendTransaction`, configurando un valor de **1 wei**. La consola devuelve un Hash de Transaccion unico (`0x99d3...`), lo cual constituye el comprobante digital de que la orden ha sido inyectada en la red y esta pendiente de ser incluida en un bloque por los validadores.

![Envio de 1 wei y hash de transaccion](https://drive.google.com/drive/folders/12YvXn2_2DJ1SvTjsv5siBEDNLpq9WJQb)

Por ultimo, tras el procesamiento de la transferencia por parte de la red, se realiza una consulta de saldo final para verificar el cumplimiento de la consigna. El sistema arroja un balance de **99.999974668 ETH**.

![Verificacion de saldo final](https://drive.google.com/drive/folders/12YvXn2_2DJ1SvTjsv5siBEDNLpq9WJQb)

### Observaciones tecnicas

- La existencia de hash de transaccion confirma la emision correcta de la orden.
- La variacion de saldo es consistente con el envio de 1 wei mas costo de gas.
- La prueba valida extremo a extremo: cuenta creada previamente, cuenta fondeada, envio y verificacion posterior.

---

## 4) Desarrollo de scripts que interactuan con la red

### Objetivo

Completar y utilizar los scripts solicitados para:

- administrar fondos y cuentas del nodo,
- inspeccionar transferencias de ether en rangos de bloques,
- filtrar por direcciones y visualizar relaciones entre cuentas.

### Funcionalidades implementadas

#### `bfa_funds.py`

- Conexion al nodo mediante IPC.
- Validacion y normalizacion de direcciones (`checksum`).
- Consulta de balance por unidad (`wei`, `Gwei`, `ether`, etc.).
- Transferencia firmada localmente con clave privada obtenida desde keystore.
- Listado de cuentas detectadas en el keystore con su saldo.

#### `show_transactions.py`

- Recorrido de bloques entre `first-block` y `last-block`.
- Consideracion de transacciones con transferencia de ether relevante.
- Filtrado opcional por una o mas direcciones de origen/destino.
- Modo `--add` para expandir dinamicamente el conjunto de direcciones relacionadas.
- Salida en formato `plain` y en formato `graphviz`.
- Opcion `--short` para truncar direcciones en la salida.

### Archivo de entorno requerido (`.env`)

Para ejecutar `bfa_funds.py` es necesario definir un archivo `.env` en la carpeta `TP/3` con la ruta al keystore del nodo. El script carga esta configuracion con `python-dotenv` y utiliza la variable `KEYSTORE_PATH` para encontrar las claves.

Ejemplo de `.env`:

```env
KEYSTORE_PATH=/home/usuario/blockchain-iua/bfatest/node/keystore
```

Notas:

- `KEYSTORE_PATH` debe apuntar a una carpeta existente.
- Si la variable no existe o la ruta es invalida, `bfa_funds.py` finaliza con error al iniciar.
- `show_transactions.py` no depende de `KEYSTORE_PATH`.

### Uso de los programas

Desde la carpeta `TP/3`:

```bash
python3 bfa_funds.py accounts
python3 bfa_funds.py balance -a 0xTU_CUENTA --unit ether
python3 bfa_funds.py transfer --from 0xORIGEN --to 0xDESTINO --amount 1 --unit wei
```

```bash
python3 show_transactions.py --first-block 0 --last-block latest --format plain
python3 show_transactions.py 0xDIRECCION1 0xDIRECCION2 --first-block 0 --last-block latest --format plain --short
python3 show_transactions.py 0xDIRECCION1 --first-block 0 --last-block latest --format graphviz --short
```

### Ejemplo de salida graphviz

La siguiente evidencia muestra un ejemplo de salida en formato graphviz para visualizacion de transferencias:

![Ejemplo de salida graphviz](https://drive.google.com/drive/folders/12YvXn2_2DJ1SvTjsv5siBEDNLpq9WJQb)

---

## Conclusiones

En este TP se completo el ciclo operativo sobre una red tipo Ethereum de prueba: primero con ejecucion y validacion de una transferencia real (punto 3), y luego con el desarrollo de herramientas de automatizacion y analisis (punto 4). Esto permitio integrar conceptos de cuentas, saldos, firma de transacciones, confirmacion en bloque y trazabilidad de movimientos en cadena.
