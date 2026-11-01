# Trabajo Final Blockchain y Contratos Inteligentes IUA 2026

**Alumno:** Vargas Benjamin

**Correo:** bvargas161@alumnos.iua.edu.ar

## Descripcion del proyecto
El sistema es una plataforma de gestión de llamados y propuestas que combina el registro en blockchain con una API encargada de sincronizar los datos y facilitar la interacción con la red. La solución se completa con un frontend que se conecta de forma directa tanto con la API como con la blockchain. En esta última entrega, se incorporaron al sistema el token ERC-20 (BENCOINS) y la implementación de dominios ENS.

## Despliegue

### Pasos para la Ejecución en Entorno Local

1. **Instalar dependecias requeridas**

2. **En una terminal ubicada en /contracts ejecutar una instancia local de la red Hardhat:**
   ```bash
   npx hardhat node
   ```
2. **En una terminal ubicada en /contracts desplegar los smartcontracts del sistema:**
   ```bash
   npx run scripts/deploy.js
   ```
    Dicho script proporcionara las direcciones de los contratos requeridas para correr la api (ver seccion "variables de entorno") y una
    frase Mnemónica para utilizar con Metamask en el frontend. Si desea puede presionar Cntrl + C para liberar la consola una vez que finalizo
    el despliegue de los contratos

3. **(Opcional) Ejecutar desde /contracts el script de fondeo de cuentas:**
   ```bash
   npx run scripts/fund_accounts.js < Mnemónico de cuenta a fondear >
   ```
    Puede utilizar el mnemónico para metamask provisto por el script de despliegue para poder probar correctamente la app web.

4. **En una nueva terminal ubicada en /api, ejecutar la API:**
   ```bash
   uvicorn api:app --port 5000
   ```
    Recordar que la api requiere que esten configuradas las variables de entorno que se pueden ver en la seccion "Variables de entorno" del presente documento
  Para mas detalles ver /api/README.md

5. **Desplegar app web desde un nuevo terminal ubicado en /web**
   ```bash
   npm run dev
   ```

  Al finalizar estos pasos el sistema estará desplegado.

## Variables de Entorno
Crear un archivo `.env` en la carpeta /api basándose en `.env.example` con los siguientes parámetros:

| Variable | Descripción | Valor ejemplo |
| --- | --- | --- |
| `WEB3_PROVIDER_URL` | URL del nodo de la Blockchain (Ganache, Infura, Alchemy, etc.) | `[http://127.0.0.1:8545](http://127.0.0.1:8545)` |
| `CFP_FACTORY_ADDRESS` | Dirección del contrato `CFPFactory` desplegado en la red | `0x112fd8b95AC6011BA4927F4420f55d7a0d517c7F` |
| `CFP_MNEMONIC` | Mnemónico de 12 palabras de la billetera de desarrollo | `cram play gadget current hint foster photo copy space panel junk nuclear` |
| `DERIVACION_PATH` | Ruta de derivación estándar de Ethereum para HD Wallets | `m/44'/60'/0'/0/0` |
| `CFP_DB_PATH` | Ruta local donde se creará y guardará la base de datos SQLite | `db/database.db` |
| `CFP_ADMIN_ADDRESS` | Dirección del administrador del sistema | `0x1c20ed4C1464c1ffb9Fd04d94779E3Da7FbefeF6` |
| `PROPOSALS_UPLOAD_DIR` | Directorio local donde se almacenarán los archivos subidos mediante la API | `uploaded_files` |
| `ENS_REGISTRY_ADDRESS` | Dirección del contrato ENS Registry desplegado en la red | `0x5FbDB2315678afecb367f032d93F642f64180aa3` |
| `ENS_RESOLVER_ADDRESS` | Dirección del contrato ENS Resolver desplegado en la red | `0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512` |
| `TOKEN_ADDRESS` | Dirección del token ERC-20 desplegado en la red (para la garantía) | `0x959922bE3CAee4b8Cd9a407cc3ac1C251C2007B1` |

Las direcciones y frases Mnemónicas podran sacarse del script de deploy de contratos (Ver carpeta /contracts)

Activar el autominado:

curl -X POST --data '{"jsonrpc":"2.0","method":"evm_setAutomine","params":[true],"id":1}' -H "Content-Type: application/json" http://127.0.0.1:8545
curl -X POST --data '{"jsonrpc":"2.0","method":"evm_setIntervalMining","params":[3000],"id":1}' -H "Content-Type: application/json" http://127.0.0.1:8545

BUGS:
- Desautorizar a un creador con llamados hace que pase a solicitudes de registro por los estados
- Arbol de merkle en front end utiliza duplicacion para hojas impares
- Comprar tokens de mas de 1000 genera error de compra, inconsistencia
