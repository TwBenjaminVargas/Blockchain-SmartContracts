# Contratos Inteligentes

## Despliegue

### Pasos para la Ejecución en Entorno Local

1. **Instalar dependecias requeridas**

3. **En una terminal ubicada en /contracts compilar los contratos:**
   ```bash
   npx hardhat compile
   ```

4. **En una terminal ubicada en /contracts ejecutar una instancia local de la red Hardhat:**
   ```bash
   npx hardhat node
   ```
5. **En una terminal ubicada en /contracts desplegar los smartcontracts del sistema:**
   ```bash
   npx run scripts/deploy.js
   ```
    Dicho script proporcionara las direcciones de los contratos requeridas para correr la api (ver seccion "variables de entorno") y una
    frase Mnemónica para utilizar con Metamask en el frontend. Si desea puede presionar Cntrl + C para liberar la consola una vez que finalizo
    el despliegue de los contratos

6. **(Opcional) Ejecutar desde /contracts el script de fondeo de cuentas:**
   ```bash
   npx run scripts/fund_accounts.js < Mnemónico de cuenta a fondear >
   ```
    Puede utilizar el mnemónico para metamask provisto por el script de despliegue para poder probar correctamente la app web.

## Ejecucion de Tests

1. **En una terminal ubicada en /contracts y con los contratos compilados ejecutar:**
   ```bash
   npx hardhat test
   ```

## Contratos
### CFPFactory

El contrato **CFPFactory** es una fábrica encargada de gestionar el registro de creadores autorizados y de instanciar y rastrear de forma centralizada nuevos contratos de convocatorias (CFP). Su función principal consiste en controlar las autorizaciones de los usuarios, permitir el registro de solicitudes pendientes y facilitar la creación de llamados a propuestas, garantizando la existencia de un identificador único para cada uno.

### CFP

El contrato **CFP** (Call For Proposals) representa un llamado o convocatoria individual en el cual los participantes pueden registrar propuestas y abonar las garantías en tokens requeridas. Cumple la función de administrar el ciclo de vida de la convocatoria, gestionando el tiempo de cierre, la recepción de archivos y la devolución o liquidación final de las garantías recibidas.

### BENCOIN

El contrato **BENCOIN** es un token fungible bajo el estándar ERC20 que incluye un mecanismo simple de compraventa utilizando Ether según una tasa de cambio predefinida. Su función principal es permitir a los usuarios minar tokens enviando Ether al contrato o vender sus tokens de regreso para recibir el valor equivalente en Ether de las reservas disponibles.

### UsuariosRegistrar

El contrato **UsuariosRegistrar** permite a los usuarios registrar subdominios en el sistema ENS de manera directa y atómica en una sola operación. Su función es asignar la propiedad del subdominio, establecer el resolutor por defecto, guardar la dirección del usuario e invocar la configuración de la resolución inversa para vincular la billetera con el nombre.

### LlamadosRegistrar

El contrato **LlamadosRegistrar** permite a los usuarios reservar y configurar la resolución de subdominios ENS asociados a contratos en un proceso de dos pasos. Su función consiste en registrar y asegurar primero la propiedad del subdominio deseado para, posteriormente, permitir al propietario configurar el resolutor y enlazar el nombre de dominio a un contrato de destino.

### ReverseRegistrar

El contrato **ReverseRegistrar** administra la asignación de nodos en el espacio de nombres de resolución inversa de ENS (`addr.reverse`). Su función principal es permitir que las cuentas de usuario y otros contratos puedan asociar sus direcciones públicas de Ethereum con nombres de dominio de texto legible de manera segura y estandarizada.

### Resolver

El contrato **Resolver** actúa como el depósito de datos que asocia nodos de ENS con sus valores de dirección o nombre de texto. Se encarga de implementar los estándares ERC-137 (resolución directa) y ERC-181 (resolución reversa), almacenando y respondiendo a las consultas de mapeo entre un nodo hash y una dirección de Ethereum o un texto de nombre de dominio.

### Registry

El contrato **Registry** funciona como el registro central del sistema de nombres ENS, manteniendo la asignación de propietarios, resolutores y tiempos de vida (TTL) para cada nodo. Su función es actuar como la base de datos authoritative que controla la estructura jerárquica de dominios y subdominios, validando los permisos del propietario antes de permitir transferencias o cambios en sus registros.