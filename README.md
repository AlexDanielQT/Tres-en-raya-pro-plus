# Tres en Raya Pro+
**Trabajo 01 — Evolución de una Arquitectura de Videojuegos**
Escuela Profesional de Ingeniería de Sistemas · Programación de Video Juegos

---

## Descripción general

Este proyecto es la evolución del Tres en Raya básico desarrollado en clase.
El objetivo **no** fue construir un videojuego desde cero, sino comprender cómo
crece y se extiende una arquitectura existente agregando nuevas características
visuales y funcionales, transformando el juego original en **Tres en Raya Pro+**.

---

## Arquitectura implementada

La arquitectura respeta estrictamente la separación de responsabilidades
presentada en clase:

```
GAME LOOP
│
├── INPUT   → EscenaTresEnRaya.input()
├── UPDATE  → EscenaTresEnRaya.update()
└── RENDER  → EscenaTresEnRaya.render()
     │
     └── EscenaTresEnRaya  (coordinadora)
          │
          ├── [Entidad Lógica]   Cursor       — posición lógica (fila, columna)
          ├── [Entidad Lógica]   TresEnRaya   — estado, reglas, turnos, ganador
          ├── [Entidad Gráfica]  Tablero      — dibuja la cuadrícula
          ├── [Entidad Gráfica]  FichaX       — dibuja la ficha X
          └── [Entidad Gráfica]  FichaO       — dibuja la ficha O
```

**Principio clave — Estado ≠ Representación:**
- `TresEnRaya` vive en los datos (matriz, turno, ganador). No dibuja nada.
- Las entidades gráficas solo saben representarse visualmente. No conocen las reglas.
- `EscenaTresEnRaya` coordina ambos mundos: traduce el estado lógico en visuales.
- El **Game Loop** organiza el ciclo `Input → Update → Render` sin excepción.

---

## Mejoras implementadas (Trabajo 01)

Cada mejora se describe comparando directamente con el código original (`3enRaya.py`).

---

### 1. Entidades Gráficas

#### FichaX (antes: clase `X`)

| Aspecto | Original | Pro+ |
|---|---|---|
| Nombre de clase | `X` | `FichaX` |
| Grosor de trazos | `1` px | `5` px (trazo principal) |
| Posición de las líneas | Esquina a esquina `(0,0)→(3e,3e)` | Con margen interior (`margen = e * 0.28`) |
| Detalle visual | Ninguno | Punto circular en cada extremo con color aclarado en `+60` |
| Animación | Sin animación | `escala_aparicion`: crece de `0.05` a `1.0` al colocarse |

La ficha original dibujaba dos líneas simples de un píxel de extremo a extremo de la celda. La versión Pro+ agrega margen para que la X no ocupe toda la celda, aumenta el grosor, dibuja un punto decorativo en cada extremo con un color más claro calculado dinámicamente, y aplica una animación de aparición progresiva escalando el lienzo antes de renderizarlo.

#### FichaO (antes: clase `O`)

| Aspecto | Original | Pro+ |
|---|---|---|
| Nombre de clase | `O` | `FichaO` |
| Circunferencias | Una sola, grosor `1` | Dos: exterior (grosor `2`, color atenuado) + interior (grosor `5`, color principal) |
| Radio | `3e/2` (ocupa toda la celda) | Exterior ajustado con margen; interior al `62%` del exterior |
| Animación | Sin animación | `escala_aparicion`: mismo mecanismo que `FichaX` |

La ficha original era un único círculo delgado que ocupaba toda la celda. La versión Pro+ introduce una doble circunferencia: la exterior usa el mismo color base reducido en 65 puntos por canal (simulando un degradado), y la interior es la principal con mayor grosor. Ambas se escalan durante la animación de aparición.

#### Tablero

| Aspecto | Original | Pro+ |
|---|---|---|
| Fondo | Sin fondo (transparente) | Fondo oscuro `(18, 18, 38)` |
| Marco exterior | Sin marco | Marco de `3` px con color `(170, 170, 200)` |
| Grosor de líneas | `1` px | `2` px |
| Celdas ganadoras | Sin resaltado | Fondo dorado semitransparente `(240, 200, 60, 45)` sobre las celdas ganadoras |

El tablero original era solo cuatro líneas blancas sobre fondo negro. La versión Pro+ agrega un fondo propio para la cuadrícula, un marco exterior visible, líneas más gruesas y la capacidad de recibir una lista de celdas ganadoras desde la Escena para resaltarlas sin conocer las reglas del juego.

#### Cursor

| Aspecto | Original | Pro+ |
|---|---|---|
| Forma | Rectángulo interior simple | Cuatro segmentos de esquina (estilo targeting) |
| Color | Amarillo fijo `(255,255,0)` pasado como parámetro | Dinámico: rojo `(220,80,80)` para X, cian `(80,200,230)` para O |
| Animación | Sin animación | Pulso suave de opacidad entre 160 y 220 usando `math.sin(_pulso)` |
| Estado de turno | No tenía | Método `setTurno()` para adaptar el color |
| `update()` | No existía | Avanza `_pulso` en cada frame |

---

### 2. Entidades Lógicas

#### TresEnRaya

| Aspecto | Original | Pro+ |
|---|---|---|
| Celdas ganadoras | No se almacenaban | Lista `celdas_ganadoras` con las `(fila, col)` que forman la línea ganadora |
| Estadísticas | No existían | `victorias_x`, `victorias_o`, `empates`, `partidas` — persisten entre reiniciadas |
| `jugar()` | Ignora si hay empate activo | Retorna `False` si ya hay empate, evitando jugadas extra |
| Métodos nuevos | — | `getCeldasGanadoras()`, `getEstadisticas()` |
| `reiniciar()` | Resetea todo | Solo resetea el estado de la partida; las estadísticas se conservan |

#### Cursor

| Aspecto | Original | Pro+ |
|---|---|---|
| `setTurno()` | No existía | Añadido para que el Cursor conozca el turno activo y adapte su color |
| `update()` | No existía | Añadido para avanzar la animación de pulso en cada frame |

---

### 3. Animaciones

| Animación | Original | Pro+ |
|---|---|---|
| Indicador de turno | Pulsación de tamaño en `xTurno` / `oTurno` (entidades X y O separadas) | Eliminado; reemplazado por panel lateral con ficha miniatura estática |
| Fichas al colocarse | Aparecen instantáneamente | Crecen desde escala `0.05` hasta `1.0` en ~12 frames (`+0.08` por frame) |
| Cursor | Estático | Pulso continuo de opacidad con `math.sin` |
| Fin de juego | Sin efecto | Parpadeo suave del mensaje usando `math.sin(_parpadeo)` |

El original animaba el tamaño de las entidades `xTurno` / `oTurno` incrementando y revirtiendo `self.e`. La versión Pro+ elimina esas entidades independientes y centraliza la información del turno en el panel lateral, mientras incorpora animaciones más relevantes: la aparición de cada ficha al ser colocada y el pulso del cursor.

---

### 4. Efectos de fin de juego

En el original, el juego simplemente dejaba de procesar input cuando había ganador o empate, sin ningún efecto visual adicional ni mensaje en pantalla.

La versión Pro+ agrega:
- Resaltado dorado semitransparente sobre las tres celdas ganadoras (gestionado por `Tablero.set_celdas_ganadoras()`).
- Ocultamiento del cursor una vez terminada la partida.
- Mensaje de fin `"¡GANA X!"`, `"¡GANA O!"` o `"EMPATE"` en el panel lateral con parpadeo animado.
- El color del mensaje corresponde al color del jugador ganador.
- Texto de ayuda `"Presiona R para reiniciar"` visible mientras el juego está terminado.

---

### 5. Panel lateral de información (nuevo)

El original no tenía panel de información. La versión Pro+ introduce `_renderPanel()` en la Escena con:
- **Indicador de turno:** nombre del jugador activo y una ficha miniatura renderizada con las mismas clases `FichaX` / `FichaO`, a escala reducida (`e // 2`).
- **Estadísticas persistentes:** partidas jugadas, victorias de X, victorias de O y empates. Se conservan al reiniciar con R.
- **Barra de controles:** texto de ayuda fijo en la parte inferior de la ventana.

---

### 6. Game Loop y ventana

| Aspecto | Original | Pro+ |
|---|---|---|
| Tamaño de ventana | `600 × 400` px | `880 × 620` px |
| Escala base (`e`) | `30` | `55` |
| Fondo | Negro `(0,0,0)` | Azul muy oscuro `(14, 14, 28)` |
| Tecla ESC | Sin manejar | Cierra el juego correctamente |
| Tecla R | Sin manejar | Reinicia la partida conservando estadísticas |
| Estructura | Código suelto al nivel del módulo | Encapsulado en función `main()` |
| `import sys` | Faltaba (bug: `sys.exit()` sin importar) | Presente y correcto |

---

## Controles

| Tecla | Acción |
|---|---|
| ↑ ↓ ← → | Mover el cursor |
| ENTER | Colocar ficha |
| R | Reiniciar partida (las estadísticas se conservan) |
| ESC / Cerrar | Salir del juego |

---

## Requisitos

- Python 3.8 o superior
- pygame

```bash
pip install pygame
```

## Ejecución

```bash
python main.py
```

---

## Estructura del código

| Clase | Tipo | Responsabilidad |
|---|---|---|
| `EntidadGrafica` | Gráfica (base) | Posición, escala, color, rotación |
| `FichaX` | Gráfica | Dibujar la ficha X con animación |
| `FichaO` | Gráfica | Dibujar la ficha O con animación |
| `Tablero` | Gráfica | Dibujar la cuadrícula y celdas ganadoras |
| `Cursor` | Lógica + Visual | Posición lógica del cursor y su render |
| `TresEnRaya` | Lógica | Estado del juego, reglas, estadísticas |
| `EscenaTresEnRaya` | Coordinadora | Input, Update, Render — puente lógica/gráfica |

---

## Trabajo 02 — Próxima etapa: Conecta 4

El siguiente trabajo consiste en demostrar que **la arquitectura construida es
reutilizable**. A partir de la base de Tres en Raya Pro+ se construirá una
versión funcional de **Conecta 4**, sin comenzar desde cero.

### Plan de reutilización

| Componente | Acción |
|---|---|
| `Game Loop` | Reutilizar sin cambios (`while True` + Input/Update/Render) |
| `EntidadGrafica` | Reutilizar como clase base para las nuevas fichas |
| `Tablero` | Adaptar a cuadrícula de 7 columnas × 6 filas |
| `Cursor` | Adaptar: solo se mueve horizontalmente (selección de columna) |
| `EscenaTresEnRaya` | Reemplazar por `EscenaConecta4` con la misma estructura |
| `TresEnRaya` | Reemplazar por `Conecta4` con las nuevas reglas |

### Cambios lógicos principales a implementar

- **Selección de columna:** el jugador elige una columna, no una casilla específica.
- **Caída de ficha:** al insertar en una columna, la ficha cae automáticamente a
  la posición libre más baja (gravedad simulada).
- **Detección de victoria:** cuatro fichas consecutivas del mismo jugador en
  horizontal, vertical, diagonal ascendente o diagonal descendente.
- **Empate:** tablero 7×6 completamente lleno sin ganador.

### Cambios gráficos principales a implementar

- Nuevo diseño del tablero con 42 celdas visibles (7×6).
- Fichas circulares de colores diferenciados por jugador.
- Cursor indicador de columna activa con cambio de color según turno.
- Indicadores de turno, ganador y empate reutilizando el panel lateral.

> La clave del Trabajo 02 no es construir un juego nuevo, sino demostrar que
> una arquitectura bien diseñada permite **construir una vez y reutilizar muchas veces**.
