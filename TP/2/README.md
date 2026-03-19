# TP 2 - Desafios Criptograficos

## Consigna

En este trabajo practico se resolvieron los siguientes desafios del sitio de la catedra:

1. **Generador de numeros pseudoaleatorios de Java**.
2. **DSA con reutilizacion de `k`**.

Referencias:

- https://cripto.iua.edu.ar/blockchain/doc/javarand.html
- https://cripto.iua.edu.ar/blockchain/doc/dsa.html

## Estructura de la solucion

- `java_integer_predictor.py`: resolucion del desafio de prediccion del PRNG de Java.
- `dsa_pkey_finder.py`: resolucion del desafio de recuperacion de clave privada DSA por reutilizacion de `k`.

---

## 1) Prediccion del generador pseudoaleatorio de Java

### Objetivo

Obtener dos salidas consecutivas del endpoint `challenge`, reconstruir el estado interno del generador (`seed`) y predecir el siguiente entero para enviarlo al endpoint `answer`.

### Enfoque implementado (`java_integer_predictor.py`)

El script replica el comportamiento de `java.util.Random` para `nextInt()`:

- Se implementa la transicion del LCG de 48 bits:
  - `seed = (seed * 0x5DEECE66D + 0xB) mod 2^48`
- Se modela la salida de 32 bits con signo tomando los bits altos del estado.
- Con dos valores consecutivos (`n1` y `n2`) se prueban las `2^16` posibilidades de los bits bajos del estado para recuperar un `seed` consistente.
- Una vez encontrado el estado valido, se avanza una iteracion mas para predecir el siguiente entero.
- El valor predicho se envia automaticamente al endpoint de respuesta.

### Observaciones tecnicas

- El ataque es viable porque el estado interno del LCG tiene 48 bits y cada salida filtra 32 bits altos, dejando solo 16 bits por fuerza bruta.
- La complejidad del paso de recuperacion es baja (`65536` intentos maximos).
- El script realiza toda la secuencia de consulta, prediccion y envio en forma automatica.

---

## 2) DSA con reutilizacion de `k`

### Objetivo

Detectar dos firmas DSA con el mismo valor `r` (lo que implica reutilizacion de `k`) y usar esa debilidad para calcular la clave privada `x`, luego enviarla al endpoint `answer`.

### Enfoque implementado (`dsa_pkey_finder.py`)

El flujo del script es:

1. Solicitar la clave publica para obtener el parametro `Q`.
2. Firmar mensajes distintos (`m_1`, `m_2`, `m_3`, ...) contra el endpoint `sign`.
3. Guardar cada firma `(r, s)` junto con su mensaje.
4. Detectar una colision en `r`.
5. Calcular:
   - `k = (H(m1) - H(m2)) * (s1 - s2)^(-1) mod q`
   - `x = r^(-1) * (k*s1 - H(m1)) mod q`
6. Enviar la clave privada recuperada al endpoint de respuesta.

### Observaciones tecnicas

- El ataque funciona porque reutilizar `k` en DSA rompe la seguridad del esquema.
- Se usa `SHA-256` sobre los mensajes para obtener los digests necesarios en las ecuaciones.
- El script corta la busqueda apenas encuentra una colision de `r`, calcula la clave y la reporta.

---

## Ejecucion

Desde la carpeta `TP/2`:

```bash
python3 java_integer_predictor.py
python3 dsa_pkey_finder.py
```

Ambos scripts consultan el servidor, resuelven el desafio y envian automaticamente la respuesta.

---

## Conclusion

En este TP se aplicaron ataques practicos sobre dos primitivas criptograficas en escenarios mal implementados: prediccion de un PRNG lineal y recuperacion de clave privada en DSA por reutilizacion de nonce. La resolucion muestra como errores de diseno o de implementacion pueden volver vulnerables sistemas que, en condiciones correctas, son seguros.
