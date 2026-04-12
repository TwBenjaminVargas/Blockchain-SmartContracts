# API REST Stamper (Python)

## Descripción de la carpeta

Esta carpeta contiene la implementación en Python del servidor API que interactúa con el contrato inteligente Stamper, junto con sus dependencias y pruebas automatizadas.

Estructura:

```text
api/python/
├── README.md
├── apiserver.py
├── requirements.txt
└── test_apiserver.py
```

## Función de cada archivo
### apiserver.py

Implementación principal del servidor Flask.

Responsabilidades principales:

- Conectarse al nodo Ethereum mediante Web3 (IPC u HTTP).
- Cargar ABI y dirección del contrato desde el archivo Stamper.json del directorio superior.
- Leer la primera cuenta del keystore local (~/.ethereum/keystore) en orden lexicográfico.
- Desbloquear la cuenta con contraseña y habilitar firmado local de transacciones.
- Exponer endpoints HTTP:
	- GET /stamped/<hash_value>
	- POST /stamp
	- GET /openapi.json
	- GET /swagger

### requirements.txt

Listado de dependencias de Python necesarias para ejecutar el servidor y las pruebas.

### test_apiserver.py

Conjunto de pruebas de integración basado en pytest. Las pruebas validan formatos, códigos de estado HTTP y comportamiento funcional de los endpoints.

Importante:

- Estas pruebas asumen que el servidor está ejecutándose en http://127.0.0.1:5000.
- Las pruebas realizan operaciones reales sobre la API (incluyendo solicitudes de sellado).


## Ejecución del servidor

Ubicado en la carpeta 4:

```bash
python3 api/python/apiserver.py -p "CONTRASENA"
```

o bien:

```bash
python3 api/python/apiserver.py -f /ruta/archivo_password.txt
```

Si se ejecuta desde esta carpeta:

```bash
python3 apiserver.py -p "CONTRASENA"
```

Notas operativas:

- El programa exige uno de los parámetros: -p/--password o -f/--password-file.
- La ruta del nodo y las rutas base del proyecto se construyen internamente en apiserver.py; por ello se recomienda ejecutar desde el contexto de la carpeta 4 para evitar ambiguedades.
- El servidor se levanta por defecto en el puerto 5000.

## Ejecución de pruebas

Con el servidor activo en otra terminal:

```bash
cd api/python
pytest -v test_apiserver.py
```

Opcionalmente, para ejecutar todo el conjunto de pruebas del directorio:

```bash
cd api/python
pytest -v
```

## Verificación manual rápida

Con el servidor activo, puede comprobarse el funcionamiento básico con curl:

```bash
curl http://127.0.0.1:5000/stamped/0x836a97e0ff6a85dd2746a39ed71171595759c02beda2d45d0280e0cd19ba3c34
```

```bash
curl -X POST http://127.0.0.1:5000/stamp \
	-H "Content-Type: application/json" \
	-d '{"hash":"0xaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}'
```
