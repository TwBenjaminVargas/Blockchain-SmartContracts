# Aplicación web cliente para Stamper

## Descripción

Esta carpeta contiene una aplicación web estática que funciona como cliente de la API REST del práctico. Su objetivo es permitir al usuario seleccionar un archivo local, calcular su hash SHA-256 en el navegador y solicitar su registro (sellado) en blockchain a través del endpoint `POST /stamp`.

La aplicación no requiere proceso de compilación ni dependencias de Node.js; se ejecuta sirviendo archivos estáticos mediante un servidor HTTP local.

## Vista previa

La siguiente imagen corresponde a la interfaz de la aplicación:

![Vista de la aplicación Web Stamper](https://lh3.googleusercontent.com/u/0/d/12cYm1PuRAIAWAmbRIR-lqIWF8gRv_62J)

## Estructura de la carpeta

```text
app web/
├── README.md
├── index.html
├── app.js
└── style.css
```

## Función de cada archivo
### `index.html`

Define la interfaz principal:

- Selector de archivo local.
- Vista previa del hash calculado.
- Opción para firmar el hash con una clave privada Ethereum.
- Botón de envío (`Stamp!`) y panel de resultados.

También carga:

- `style.css` para estilos visuales.
- `app.js` para la lógica de interacción.
- `ethers.js` (desde CDN) para la firma opcional en el navegador.

### `app.js`

Implementa el comportamiento funcional de la interfaz:

- Calcula SHA-256 del archivo seleccionado mediante `crypto.subtle.digest`.
- Construye el payload JSON con el campo `hash`.
- Firma opcionalmente el hash si el usuario provee clave privada.
- Invoca `POST http://127.0.0.1:5000/stamp`.
- Muestra resultados exitosos y mensajes de error en pantalla.

### `style.css`

Proporciona la presentación visual de la interfaz: tipografías, distribución, estados de botones y estilos para los mensajes de resultado.

## Requisitos de ejecución

Para utilizar esta aplicación deben cumplirse dos condiciones:

1. El servidor de API debe estar en ejecución en `http://127.0.0.1:5000`.
2. Debe levantarse un servidor HTTP local en esta carpeta (abrir `index.html` directamente con `file://` no es recomendable para este flujo).

## Cómo ejecutar la aplicación

Desde esta carpeta:

```bash
cd "/home/ben/Documentos/ByCI/TP/4/app web"
python3 -m http.server 8000
```

Luego abrir en el navegador:

```text
http://127.0.0.1:8000
```

## Flujo de uso

1. Seleccionar un archivo desde el botón "Seleccionar desde archivos".
2. Verificar que se muestre el hash SHA-256 calculado.
3. Opcional: activar "Firmar con clave privada" e ingresar una clave privada válida.
4. Presionar "Stamp!" para enviar la solicitud a la API.
5. Revisar el resultado:
	- Si el hash se registró correctamente, se informa bloque y transacción.
	- Si ya estaba registrado, se muestran bloque y firmante existentes.
	- Si hay error de formato o conexión, se muestra el mensaje correspondiente.

## Consideraciones técnicas

- La URL de la API está fijada en `app.js` como `http://127.0.0.1:5000`.
- La firma se realiza del lado cliente mediante `ethers.Wallet.signMessage`.
- La clave privada ingresada se usa en memoria durante la operación y no se persiste en archivos.

## Verificación rápida

Con API y servidor web activos:

1. Abrir la aplicación en el navegador.
2. Cargar cualquier archivo de prueba.
3. Ejecutar un sellado sin firma.
4. Repetir el sellado del mismo archivo para comprobar la respuesta de conflicto (`hash` ya registrado).

