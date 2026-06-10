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

### 1. Entidades Gráficas mejoradas

**FichaX**
- Diseño con dos trazos diagonales estilizados de grosor variable.
- Puntos decorativos en los extremos con color más claro.
- Animación de aparición: la ficha crece desde escala 0 hasta 1.0 al ser colocada.
- Soporte de rotación mediante transformaciones geométricas (`pygame.transform.rotate`).

**FichaO**
- Diseño de doble circunferencia: exterior con color atenuado, interior con color principal.
- Animación de aparición idéntica a FichaX (escala progresiva desde cero).
- Soporte de rotación.

**Tablero**
- Fondo oscuro diferenciado del resto de la pantalla.
- Marco exterior visible con color personalizable.
- Resaltado suave de las celdas ganadoras (fondo dorado semitransparente).
- Separación visual clara entre la cuadrícula y el panel lateral.

**Cursor**
- Cambia de color según el jugador activo: rojo para X, cian para O.
- Diseño de cuatro segmentos de esquina (en lugar de un rectángulo simple).
- Efecto pulsante suave: la opacidad oscila usando `math.sin`.

### 2. Entidades Lógicas mejoradas

**TresEnRaya**
- Mantiene y valida la matriz 3×3.
- Gestiona los turnos y el cambio automático entre jugadores.
- Detecta ganador en filas, columnas y ambas diagonales.
- Almacena las celdas ganadoras para comunicarlas a la capa gráfica.
- Detecta empate cuando el tablero está lleno sin ganador.
- **Estadísticas acumuladas** entre partidas: contador de partidas, victorias de X, victorias de O y empates.

**Cursor**
- Trabaja en coordenadas lógicas (fila, columna). La Escena transforma a píxeles.
- Límites de movimiento correctos: no sale de la cuadrícula.
- Estado de turno para adaptar su color visual.

### 3. Animaciones

- **Fichas:** aparición progresiva desde tamaño cero al ser colocadas (`escala_aparicion` de 0.05 → 1.0).
- **Cursor:** pulso continuo de opacidad mediante `math.sin` actualizado en cada frame.
- **Mensaje de fin de juego:** parpadeo suave con transparencia variable.

### 4. Efectos de fin de juego

- Las celdas ganadoras se resaltan con un fondo dorado semitransparente en el tablero.
- Mensaje de victoria o empate visible en el panel lateral con parpadeo animado.
- El color del mensaje coincide con el color del jugador ganador.
- Indicación de cómo reiniciar la partida.

### 5. Panel de información

- Indicador del turno activo con ficha miniatura renderizada en tiempo real.
- Panel de estadísticas persistentes (no se borran al reiniciar la partida).
- Barra de ayuda de controles en la parte inferior de la pantalla.

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
