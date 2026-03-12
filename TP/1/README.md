# TP 1 — Desafíos Criptográficos

## Consigna

En este trabajo práctico se resolvieron dos desafíos criptográficos:

1. **Búsqueda de una colisión** en una función de hash (SHA-256 truncada).
2. **Prueba de trabajo (Proof of Work)** sobre una red blockchain ficticia.

## Estructura de la solución

- `collision_finder.py`: resolución del desafío de colisión SHA-256-48.
- `PoW.py`: resolución del desafío de minado de bloque (PoW).

---

## 1) Búsqueda de colisión (SHA-256-48)

### Objetivo

Encontrar dos mensajes distintos `message1` y `message2` tales que los **primeros 48 bits** del hash SHA-256 sean iguales.

### Enfoque implementado (`collision_finder.py`)

Se utilizó un enfoque probabilístico por **cumpleaños (birthday attack)**:

- Se generan mensajes del tipo `EMAIL + i`.
- Para cada mensaje, se calcula `SHA-256` y se truncan los primeros 12 caracteres hexadecimales (48 bits).
- Se almacena cada hash truncado en un diccionario (`seen`).
- Cuando aparece un hash ya existente, se obtiene una colisión válida entre dos mensajes distintos.

### Observaciones técnicas

- El método evita búsqueda exhaustiva completa y aprovecha la complejidad esperada del ataque de cumpleaños.
- El tiempo de ejecución depende de la suerte estadística y del rendimiento de la máquina.
- Una vez encontrada la colisión, el script la envía automáticamente al endpoint provisto por el servidor.

---

## 2) Prueba de trabajo en blockchain ficticia

### Objetivo

Construir un bloque válido cuyo hash SHA-256 cumpla la condición:

`hash(nuevo_bloque) < target`

donde `target` está definido por el bloque previo.

### Enfoque implementado (`PoW.py`)

El flujo de trabajo es:

1. Solicitar al servidor el último bloque de la cadena.
2. Decodificar su contenido en base64 y extraer:
	- número de bloque,
	- timestamp,
	- target,
	- hash del bloque previo.
3. Armar un nuevo bloque de 96 bytes con:
	- `new_block_number = prev + 1`,
	- timestamp actual,
	- mismo target,
	- nonce inicial,
	- hash del bloque previo,
	- hash SHA-256 del email.
4. Iterar sobre el `nonce` hasta que el hash del bloque sea menor al target.
5. Si pasa un intervalo de tiempo sin solución, actualizar timestamp y reiniciar nonce para mantener validez temporal.
6. Enviar el bloque minado al servidor.

### Observaciones técnicas

- Se implementó validación y visualización de campos del bloque para facilitar trazabilidad.
- El cuello de botella está en la cantidad de intentos de nonce, por lo que el tiempo final depende de la dificultad (`target`).
- La solución respeta el formato de bloque esperado por el servicio remoto.

---


## Ejecución

Desde la carpeta `TP/1`:

```bash
python3 collision_finder.py
python3 PoW.py
```

Ambos scripts solicitan el email por consola y realizan el envío automático de la respuesta al servidor de la materia.

---

## Conclusión

En este TP se aplicaron conceptos fundamentales de criptografía aplicada: propiedades de funciones hash (resistencia a colisiones en dominios truncados) y mecanismo de consenso por prueba de trabajo. La implementación permitió observar, en un entorno práctico, cómo la complejidad computacional y los parámetros del sistema impactan directamente en la factibilidad de cada ataque/proceso.
