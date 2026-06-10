"""
╔══════════════════════════════════════════════════════════════╗
║            TRES EN RAYA PRO+  —  Trabajo 01                  ║
║   Escuela Profesional de Ingeniería de Sistemas              ║
║   Programación de Video Juegos                               ║
╚══════════════════════════════════════════════════════════════╝

Arquitectura implementada (según "Arquitectura Básica de un Videojuego"):

  GAME LOOP
  │
  ├── INPUT   → EscenaTresEnRaya.input()
  ├── UPDATE  → EscenaTresEnRaya.update()
  └── RENDER  → EscenaTresEnRaya.render()
       │
       └── EscenaTresEnRaya  (coordinadora)
            │
            ├── [Entidad Lógica]   Cursor      — posición lógica (fila, columna)
            ├── [Entidad Lógica]   TresEnRaya  — estado, reglas, turnos, ganador
            ├── [Entidad Gráfica]  Tablero     — dibuja la cuadrícula
            ├── [Entidad Gráfica]  FichaX      — dibuja la ficha X
            └── [Entidad Gráfica]  FichaO      — dibuja la ficha O

Principio clave: Estado ≠ Representación
  - TresEnRaya vive en los datos (matriz, turno, ganador).
  - Las entidades gráficas solo saben dibujarse.
  - La Escena coordina ambos mundos.

Controles:
  Flechas     → mover cursor
  ENTER       → colocar ficha
  R           → reiniciar partida (estadísticas persisten)
  ESC / Cerrar → salir
"""

import math
import sys

import pygame

# ═══════════════════════════════════════════════════════════════════
#  ENTIDADES GRÁFICAS
#  Responsabilidad única: representar visualmente un elemento.
#  NO conocen reglas, turnos ni el estado del juego.
# ═══════════════════════════════════════════════════════════════════


class EntidadGrafica:
    """
    Clase base para todas las entidades gráficas.
    Sabe: dibujarse, cambiar color, trasladarse, escalarse, rotarse.
    NO sabe: quién ganó, de quién es el turno, cuáles son las reglas.
    """

    def __init__(self, x, y, e):
        self.x = x
        self.y = y
        self.e = e  # escala base (unidades lógicas → píxeles)
        self.alfa = 0  # ángulo de rotación (grados)
        self.color = (255, 255, 255)

    def setColor(self, color):
        self.color = color

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def setEscala(self, e):
        self.e = e

    def render(self, pantalla):
        """Cada subclase implementa su propia representación visual."""
        raise NotImplementedError


class FichaX(EntidadGrafica):
    """
    Entidad Gráfica: ficha X.
    Representación: dos líneas diagonales con un trazo decorativo interior.
    Animación de aparición: escala_aparicion crece de 0 a 1 al ser colocada.
    """

    GROSOR = 5
    GROSOR_INTERIOR = 2

    def __init__(self, x, y, e):
        super().__init__(x, y, e)
        self.escala_aparicion = 1.0  # 0.0 → invisible, 1.0 → completa

    def render(self, pantalla):
        e = self.e
        escala = max(0.01, self.escala_aparicion)
        tam = int(3 * e * escala)
        if tam < 3:
            return

        lienzo = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)

        margen = e * 0.28
        x0, y0 = margen, margen
        x1, y1 = 3 * e - margen, 3 * e - margen

        # Trazo principal
        pygame.draw.line(lienzo, self.color, (x0, y0), (x1, y1), self.GROSOR)
        pygame.draw.line(lienzo, self.color, (x1, y0), (x0, y1), self.GROSOR)

        # Pequeño punto en cada extremo (detalle visual discreto)
        color_extremo = tuple(min(255, c + 60) for c in self.color)
        radio = max(2, int(e * 0.10))
        for px, py in [(x0, y0), (x1, y1), (x1, y0), (x0, y1)]:
            pygame.draw.circle(lienzo, color_extremo, (int(px), int(py)), radio)

        # Aplicar escala de aparición (efecto "crecimiento desde cero")
        if escala < 1.0:
            lienzo_escalado = pygame.transform.scale(lienzo, (tam, tam))
            destino = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)
            offset = (3 * e - tam) // 2
            destino.blit(lienzo_escalado, (offset, offset))
            lienzo = destino

        # Transformación geométrica: rotación
        rotado = pygame.transform.rotate(lienzo, self.alfa)
        rect = rotado.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotado, rect)


class FichaO(EntidadGrafica):
    """
    Entidad Gráfica: ficha O.
    Representación: circunferencia exterior atenuada + circunferencia interior.
    Animación de aparición: escala_aparicion crece de 0 a 1 al ser colocada.
    """

    GROSOR_EXT = 2
    GROSOR_INT = 5

    def __init__(self, x, y, e):
        super().__init__(x, y, e)
        self.escala_aparicion = 1.0

    def render(self, pantalla):
        e = self.e
        escala = max(0.01, self.escala_aparicion)
        tam = int(3 * e * escala)
        if tam < 3:
            return

        lienzo = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)

        cx = int(3 * e / 2)
        cy = int(3 * e / 2)
        radio_ext = int(3 * e / 2 - e * 0.18)
        radio_int = int(radio_ext * 0.62)

        # Circunferencia exterior (color atenuado)
        color_ext = tuple(max(0, c - 65) for c in self.color)
        pygame.draw.circle(lienzo, color_ext, (cx, cy), radio_ext, self.GROSOR_EXT)

        # Circunferencia interior (color principal)
        pygame.draw.circle(lienzo, self.color, (cx, cy), radio_int, self.GROSOR_INT)

        # Aplicar escala de aparición
        if escala < 1.0:
            lienzo_escalado = pygame.transform.scale(lienzo, (tam, tam))
            destino = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)
            offset = (3 * e - tam) // 2
            destino.blit(lienzo_escalado, (offset, offset))
            lienzo = destino

        # Transformación geométrica: rotación
        rotado = pygame.transform.rotate(lienzo, self.alfa)
        rect = rotado.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotado, rect)


class Tablero(EntidadGrafica):
    """
    Entidad Gráfica: cuadrícula del juego.
    Representa visualmente la cuadrícula 3×3.
    No conoce ninguna regla del Tres en Raya.
    Acepta celdas_ganadoras para resaltarlas (dato gráfico, no lógico).
    """

    GROSOR_LINEA = 2
    GROSOR_MARCO = 3

    def __init__(self, x, y, e):
        super().__init__(x, y, e)
        self.color_marco = (170, 170, 200)
        self.color_fondo = (18, 18, 38)
        self.color_ganador = (240, 200, 60)
        self.celdas_ganadoras = []  # lista de (fila, col) a resaltar

    def set_celdas_ganadoras(self, celdas):
        """Recibe desde la escena qué celdas resaltar (información viene de la lógica)."""
        self.celdas_ganadoras = celdas if celdas else []

    def render(self, pantalla):
        e = self.e
        size = 9 * e
        mg = self.GROSOR_MARCO

        lienzo = pygame.Surface((size + 2 * mg, size + 2 * mg), pygame.SRCALPHA)

        # Fondo de la cuadrícula
        pygame.draw.rect(lienzo, self.color_fondo, (mg, mg, size, size))

        # Resaltado suave de las celdas ganadoras
        for fila, col in self.celdas_ganadoras:
            rx = mg + col * 3 * e + 3
            ry = mg + fila * 3 * e + 3
            pygame.draw.rect(
                lienzo,
                (*self.color_ganador, 45),
                (rx, ry, 3 * e - 6, 3 * e - 6),
            )

        # Líneas internas de la cuadrícula (primitivas gráficas)
        for i in [1, 2]:
            pygame.draw.line(
                lienzo,
                self.color,
                (mg + i * 3 * e, mg),
                (mg + i * 3 * e, mg + size),
                self.GROSOR_LINEA,
            )
            pygame.draw.line(
                lienzo,
                self.color,
                (mg, mg + i * 3 * e),
                (mg + size, mg + i * 3 * e),
                self.GROSOR_LINEA,
            )

        # Marco exterior
        pygame.draw.rect(
            lienzo,
            self.color_marco,
            (0, 0, size + 2 * mg, size + 2 * mg),
            self.GROSOR_MARCO,
        )

        # Transformación geométrica: rotación
        rotado = pygame.transform.rotate(lienzo, self.alfa)
        rect = rotado.get_rect(topleft=(self.x - mg, self.y - mg))
        pantalla.blit(rotado, rect)


# ═══════════════════════════════════════════════════════════════════
#  ENTIDADES LÓGICAS
#  Responsabilidad: administrar información y reglas.
#  NO dibujan, NO capturan teclado, NO crean ventanas.
# ═══════════════════════════════════════════════════════════════════


class Cursor:
    """
    Entidad Lógica: posición de selección del jugador.
    Trabaja en coordenadas lógicas (fila, columna), no en píxeles.
    La Escena convierte fila/columna → x/y para dibujarlo.

    Mundo lógico:  fila, columna
         ↓  (transformación en la Escena)
    Mundo gráfico: x, y  →  Render
    """

    def __init__(self, fila, columna):
        self.fila = fila
        self.columna = columna
        self.turno = 1  # 1 = X, 2 = O  (para color visual)
        self._pulso = 0.0  # controla animación pulsante
        self._pulso_vel = 0.05  # velocidad discreta del pulso

    # ── Movimiento (modifica el estado lógico) ───────────────────
    def moverArriba(self):
        if self.fila > 0:
            self.fila -= 1

    def moverAbajo(self):
        if self.fila < 2:
            self.fila += 1

    def moverIzquierda(self):
        if self.columna > 0:
            self.columna -= 1

    def moverDerecha(self):
        if self.columna < 2:
            self.columna += 1

    # ── Accesores ───────────────────────────────────────────────
    def getFila(self):
        return self.fila

    def getColumna(self):
        return self.columna

    def getPosicion(self):
        return (self.fila, self.columna)

    def setTurno(self, turno):
        self.turno = turno

    # ── Update: avanza la animación ─────────────────────────────
    def update(self):
        self._pulso += self._pulso_vel

    # ── Render: la Escena pasa las coordenadas x, y ya calculadas
    def render(self, pantalla, x, y, e):
        """
        Dibuja el cursor como cuatro segmentos de esquina.
        Colores: rojo para X, cian para O.
        Pulso discreto: la opacidad varía levemente.
        """
        COLOR_X = (220, 80, 80)
        COLOR_O = (80, 200, 230)
        color = COLOR_X if self.turno == 1 else COLOR_O

        # Pulso muy suave: opacidad entre 160 y 220
        alpha = int(160 + 60 * math.sin(self._pulso))
        r, g, b = color
        color_a = (r, g, b, alpha)

        tam_celda = 3 * e
        margen = int(e * 0.25)
        largo_seg = int(tam_celda * 0.22)
        grosor = max(2, int(e * 0.10))

        lienzo = pygame.Surface((tam_celda, tam_celda), pygame.SRCALPHA)

        esquinas = [
            (margen, margen, +1, +1),
            (tam_celda - margen, margen, -1, +1),
            (margen, tam_celda - margen, +1, -1),
            (tam_celda - margen, tam_celda - margen, -1, -1),
        ]
        for ex, ey, dh, dv in esquinas:
            pygame.draw.line(
                lienzo, color_a, (ex, ey), (ex + dh * largo_seg, ey), grosor
            )
            pygame.draw.line(
                lienzo, color_a, (ex, ey), (ex, ey + dv * largo_seg), grosor
            )

        pantalla.blit(lienzo, (x, y))


class TresEnRaya:
    """
    Entidad Lógica central: estado y reglas del juego.

    Responsabilidades:
      - Mantener la matriz 3×3.
      - Gestionar los turnos.
      - Validar jugadas.
      - Detectar ganador (y almacenar las celdas ganadoras).
      - Detectar empate.
      - Mantener estadísticas acumuladas entre partidas.

    NO hace:
      - Dibujar gráficos.
      - Capturar teclado.
      - Crear ventanas.
      - Realizar renderizado.
    """

    VACIO = 0
    FICHA_X = 1
    FICHA_O = 2

    def __init__(self):
        self._inicializar_estado()
        # Estadísticas persisten entre partidas
        self.victorias_x = 0
        self.victorias_o = 0
        self.empates = 0
        self.partidas = 0

    # ── Inicialización del estado ────────────────────────────────
    def _inicializar_estado(self):
        self.matriz = [
            [self.VACIO, self.VACIO, self.VACIO],
            [self.VACIO, self.VACIO, self.VACIO],
            [self.VACIO, self.VACIO, self.VACIO],
        ]
        self.turno = self.FICHA_X
        self.ganador = self.VACIO
        self.celdas_ganadoras = []

    # ── Accesores del estado ─────────────────────────────────────
    def getMatriz(self):
        return self.matriz

    def getTurno(self):
        return self.turno

    def getGanador(self):
        return self.ganador

    def getCeldasGanadoras(self):
        return self.celdas_ganadoras

    def getEstadisticas(self):
        return {
            "partidas": self.partidas,
            "victorias_x": self.victorias_x,
            "victorias_o": self.victorias_o,
            "empates": self.empates,
        }

    # ── Jugada ──────────────────────────────────────────────────
    def jugar(self, fila, columna):
        """Intenta colocar la ficha del turno actual. Retorna True si fue válida."""
        if self.ganador != self.VACIO:
            return False
        if self.hayEmpate():
            return False
        if self.matriz[fila][columna] != self.VACIO:
            return False

        self.matriz[fila][columna] = self.turno
        self._verificarGanador()

        if self.ganador != self.VACIO:
            self.partidas += 1
            if self.ganador == self.FICHA_X:
                self.victorias_x += 1
            else:
                self.victorias_o += 1
        elif self.hayEmpate():
            self.partidas += 1
            self.empates += 1
        else:
            # Cambio de turno
            self.turno = self.FICHA_O if self.turno == self.FICHA_X else self.FICHA_X

        return True

    # ── Verificación de ganador ──────────────────────────────────
    def _verificarGanador(self):
        m = self.matriz

        # Filas
        for f in range(3):
            if m[f][0] != self.VACIO and m[f][0] == m[f][1] == m[f][2]:
                self.ganador = m[f][0]
                self.celdas_ganadoras = [(f, 0), (f, 1), (f, 2)]
                return

        # Columnas
        for c in range(3):
            if m[0][c] != self.VACIO and m[0][c] == m[1][c] == m[2][c]:
                self.ganador = m[0][c]
                self.celdas_ganadoras = [(0, c), (1, c), (2, c)]
                return

        # Diagonal principal
        if m[0][0] != self.VACIO and m[0][0] == m[1][1] == m[2][2]:
            self.ganador = m[0][0]
            self.celdas_ganadoras = [(0, 0), (1, 1), (2, 2)]
            return

        # Diagonal secundaria
        if m[0][2] != self.VACIO and m[0][2] == m[1][1] == m[2][0]:
            self.ganador = m[0][2]
            self.celdas_ganadoras = [(0, 2), (1, 1), (2, 0)]
            return

    # ── Empate ──────────────────────────────────────────────────
    def hayEmpate(self):
        if self.ganador != self.VACIO:
            return False
        return all(self.matriz[f][c] != self.VACIO for f in range(3) for c in range(3))

    # ── Reinicio ────────────────────────────────────────────────
    def reiniciar(self):
        """Reinicia la partida; las estadísticas acumuladas se conservan."""
        self._inicializar_estado()


# ═══════════════════════════════════════════════════════════════════
#  ESCENA PRINCIPAL
#  Coordina todas las entidades.
#  Es el "organismo" que el Game Loop mantiene vivo.
#
#  La Escena decide:
#    - Qué actualizar  (update)
#    - Qué dibujar     (render)
#    - Cómo responder al usuario (input)
# ═══════════════════════════════════════════════════════════════════


class EscenaTresEnRaya:
    """
    Coordinadora de todas las entidades del juego.

    Contiene:
      Entidades Lógicas  → Cursor, TresEnRaya
      Entidades Gráficas → Tablero, FichaX, FichaO  (se instancian en render)

    El flujo es siempre:
        input() → update() → render()
    """

    COLOR_X = (220, 80, 80)  # rojo  — jugador X
    COLOR_O = (80, 200, 230)  # cián  — jugador O
    COLOR_UI = (190, 190, 210)  # texto neutro del panel

    def __init__(self):
        self.e = 55  # escala: 1 unidad lógica = 55 px

        # ── Entidad Gráfica ─────────────────────────────────────
        margen = 60
        self.tablero = Tablero(margen, margen, self.e)
        self.tablero.setColor((185, 185, 215))

        # ── Entidades Lógicas ────────────────────────────────────
        self.cursor = Cursor(1, 1)
        self.juego = TresEnRaya()

        # ── Estado de animaciones de fichas ──────────────────────
        # { (fila, col): escala_aparicion }  — solo mientras animan
        self._escala_fichas: dict = {}

        # ── Parpadeo del mensaje final ───────────────────────────
        self._parpadeo = 0.0
        self._parpadeo_vel = 0.06  # más lento → más discreto

    # ════════════════════════════════════════════════════════════
    #  INPUT — captura la interacción del usuario
    # ════════════════════════════════════════════════════════════
    def input(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if self.hayGanador() or self.hayEmpate():
            return

        if evento.key == pygame.K_UP:
            self.cursor.moverArriba()
        elif evento.key == pygame.K_DOWN:
            self.cursor.moverAbajo()
        elif evento.key == pygame.K_LEFT:
            self.cursor.moverIzquierda()
        elif evento.key == pygame.K_RIGHT:
            self.cursor.moverDerecha()

        elif evento.key == pygame.K_RETURN:
            fila = self.cursor.getFila()
            columna = self.cursor.getColumna()

            if self.juego.jugar(fila, columna):
                # Iniciar animación de aparición para la ficha recién colocada
                self._escala_fichas[(fila, columna)] = 0.05
                # Actualizar el cursor al nuevo turno
                self.cursor.setTurno(self.juego.getTurno())

    # ════════════════════════════════════════════════════════════
    #  UPDATE — actualiza el estado interno y las animaciones
    # ════════════════════════════════════════════════════════════
    def update(self):
        # Avanza la animación del cursor
        self.cursor.update()

        # Avanza la animación de aparición de cada ficha nueva
        terminadas = []
        for clave, escala in self._escala_fichas.items():
            nueva = min(1.0, escala + 0.08)
            self._escala_fichas[clave] = nueva
            if nueva >= 1.0:
                terminadas.append(clave)
        for k in terminadas:
            del self._escala_fichas[k]

        # Pasa al tablero las celdas ganadoras para que las resalte
        # (puente lógica → gráfica, coordinado por la Escena)
        self.tablero.set_celdas_ganadoras(self.juego.getCeldasGanadoras())

        # Avanza el parpadeo del mensaje de fin de juego
        if self.hayGanador() or self.hayEmpate():
            self._parpadeo += self._parpadeo_vel

    # ════════════════════════════════════════════════════════════
    #  RENDER — representa visualmente el estado actual
    # ════════════════════════════════════════════════════════════
    def render(self, pantalla):
        # 1. Tablero (entidad gráfica)
        self.tablero.render(pantalla)

        # 2. Cursor (solo si el juego sigue activo)
        #    Transformación: coordenadas lógicas → píxeles
        if not self.hayGanador() and not self.hayEmpate():
            cx = self.tablero.x + self.cursor.getColumna() * 3 * self.e
            cy = self.tablero.y + self.cursor.getFila() * 3 * self.e
            self.cursor.render(pantalla, cx, cy, self.e)

        # 3. Fichas (entidades gráficas instanciadas según el estado lógico)
        #    La Escena consulta la matriz (estado) y decide qué dibujar.
        matriz = self.juego.getMatriz()
        for fila in range(3):
            for columna in range(3):
                # Transformación: (fila, columna) → (x, y)
                x = self.tablero.x + columna * 3 * self.e
                y = self.tablero.y + fila * 3 * self.e

                escala = self._escala_fichas.get((fila, columna), 1.0)

                if matriz[fila][columna] == TresEnRaya.FICHA_X:
                    ficha = FichaX(x, y, self.e)
                    ficha.setColor(self.COLOR_X)
                    ficha.escala_aparicion = escala
                    ficha.render(pantalla)

                elif matriz[fila][columna] == TresEnRaya.FICHA_O:
                    ficha = FichaO(x, y, self.e)
                    ficha.setColor(self.COLOR_O)
                    ficha.escala_aparicion = escala
                    ficha.render(pantalla)

        # 4. Panel lateral de información
        self._renderPanel(pantalla)

    # ────────────────────────────────────────────────────────────
    def _renderPanel(self, pantalla):
        """Dibuja el panel derecho: turno, estadísticas y ayuda."""
        e = self.e
        panel_x = self.tablero.x + 9 * e + 45
        fuente = pygame.font.SysFont("consolas", 24, bold=True)
        fuente_sm = pygame.font.SysFont("consolas", 19)

        # ── Indicador de turno ───────────────────────────────────
        if not self.hayGanador() and not self.hayEmpate():
            turno = self.juego.getTurno()
            color_turno = self.COLOR_X if turno == TresEnRaya.FICHA_X else self.COLOR_O
            nombre_turno = "Turno:  X" if turno == TresEnRaya.FICHA_X else "Turno:  O"
            lbl = fuente.render(nombre_turno, True, color_turno)
            pantalla.blit(lbl, (panel_x, 90))

            # Fichas miniatura de turno (entidades gráficas reutilizadas)
            if turno == TresEnRaya.FICHA_X:
                fx = FichaX(panel_x, 130, e // 2)
                fx.setColor(self.COLOR_X)
                fx.render(pantalla)
            else:
                fo = FichaO(panel_x, 130, e // 2)
                fo.setColor(self.COLOR_O)
                fo.render(pantalla)

        # ── Estadísticas ─────────────────────────────────────────
        est = self.juego.getEstadisticas()
        y_est = 230
        lbl2 = fuente.render("Estadísticas", True, self.COLOR_UI)
        pantalla.blit(lbl2, (panel_x, y_est))
        y_est += 32

        lineas = [
            (f"Partidas : {est['partidas']}", self.COLOR_UI),
            (f"X gana  : {est['victorias_x']}", self.COLOR_X),
            (f"O gana  : {est['victorias_o']}", self.COLOR_O),
            (f"Empates : {est['empates']}", (220, 200, 80)),
        ]
        for texto, color in lineas:
            pantalla.blit(fuente_sm.render(texto, True, color), (panel_x, y_est))
            y_est += 26

        # ── Mensaje de fin de juego (parpadeo suave) ─────────────
        ganador = self.hayGanador()
        if ganador == TresEnRaya.FICHA_X:
            self._dibujarMensajeFin(pantalla, "¡GANA X!", self.COLOR_X, panel_x)
        elif ganador == TresEnRaya.FICHA_O:
            self._dibujarMensajeFin(pantalla, "¡GANA O!", self.COLOR_O, panel_x)
        elif self.hayEmpate():
            self._dibujarMensajeFin(pantalla, "EMPATE", (220, 200, 80), panel_x)

        # ── Ayuda de controles ───────────────────────────────────
        ayuda_y = pantalla.get_height() - 42
        ayuda = fuente_sm.render(
            "Flechas: mover  |  ENTER: colocar  |  R: reiniciar  |  ESC: salir",
            True,
            (110, 110, 130),
        )
        pantalla.blit(ayuda, (35, ayuda_y))

    def _dibujarMensajeFin(self, pantalla, texto, color, panel_x):
        """Mensaje de fin de juego con parpadeo suave."""
        alpha = int(140 + 100 * math.sin(self._parpadeo))
        fuente_grande = pygame.font.SysFont("consolas", 46, bold=True)
        fuente_sm = pygame.font.SysFont("consolas", 20)

        sup = fuente_grande.render(texto, True, color)
        sup.set_alpha(alpha)
        pantalla.blit(sup, (panel_x, 380))

        hint = fuente_sm.render("Presiona  R  para", True, (170, 170, 170))
        pantalla.blit(hint, (panel_x, 435))
        hint2 = fuente_sm.render("reiniciar", True, (170, 170, 170))
        pantalla.blit(hint2, (panel_x + 20, 456))

    # ════════════════════════════════════════════════════════════
    #  Consultas de estado (delegadas a la entidad lógica)
    # ════════════════════════════════════════════════════════════
    def hayGanador(self):
        return self.juego.getGanador()

    def hayEmpate(self):
        return self.juego.hayEmpate()

    # ════════════════════════════════════════════════════════════
    #  Reinicio
    # ════════════════════════════════════════════════════════════
    def reiniciar(self):
        self.juego.reiniciar()
        self.cursor = Cursor(1, 1)
        self._escala_fichas = {}
        self._parpadeo = 0.0
        self.tablero.set_celdas_ganadoras([])


# ═══════════════════════════════════════════════════════════════════
#  GAME LOOP — el corazón del videojuego
#
#  Mientras el corazón late, el juego permanece vivo.
#
#  Analogía (del PDF):
#    Entidades  = órganos
#    Escena     = organismo
#    Game Loop  = corazón
# ═══════════════════════════════════════════════════════════════════


def main():
    pygame.init()

    ANCHO = 880
    ALTO = 620
    FPS = 60
    COLOR_FONDO = (14, 14, 28)

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Tres en Raya Pro+  —  Trabajo 01")

    clock = pygame.time.Clock()

    # La escena es el organismo que el Game Loop mantiene vivo
    escena = EscenaTresEnRaya()

    # ── GAME LOOP ────────────────────────────────────────────────
    while True:
        # ── INPUT: captura la interacción del usuario ────────────
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if evento.key == pygame.K_r:
                    escena.reiniciar()

            escena.input(evento)

        # ── UPDATE: actualiza el estado interno ──────────────────
        escena.update()

        # ── RENDER: representa visualmente el estado actual ──────
        pantalla.fill(COLOR_FONDO)
        escena.render(pantalla)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()
