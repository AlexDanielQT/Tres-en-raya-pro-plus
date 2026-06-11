"""
╔══════════════════════════════════════════════════════════════╗
║            CONECTA 4  —  Trabajo 02                          ║
║   Escuela Profesional de Ingeniería de Sistemas              ║
║   Programación de Video Juegos                               ╠═══════════════════════════════╗
║                                                              ║  REUTILIZACIÓN DE             ║
║   Base: Arquitectura de Tres en Raya Pro+ (Trabajo 01)       ║  ARQUITECTURA                 ║
╚══════════════════════════════════════════════════════════════╩═══════════════════════════════╝

ANÁLISIS DE REUTILIZACIÓN:
─────────────────────────────────────────────────────────────────
  REUTILIZADO SIN CAMBIOS:
    ✔ EntidadGrafica      — clase base, sin tocar
    ✔ FichaX / FichaO     — mismas fichas, mismo render
    ✔ Game Loop (main)    — while True, Input→Update→Render
    ✔ Estructura Input/Update/Render en la Escena

  ADAPTADO:
    ✔ Cursor              — ahora solo se mueve horizontal (columnas)
    ✔ Tablero             — 7 columnas × 6 filas (era 3×3), fondo azul oscuro

  REEMPLAZADO:
    ✔ TresEnRaya          → Conecta4  (nueva lógica: caída, victoria en 4)
    ✔ EscenaTresEnRaya    → EscenaConecta4

─────────────────────────────────────────────────────────────────
ARQUITECTURA :

  GAME LOOP
  │
  ├── INPUT   → EscenaConecta4.input()
  ├── UPDATE  → EscenaConecta4.update()
  └── RENDER  → EscenaConecta4.render()
       │
       └── EscenaConecta4  (coordinadora)
            │
            ├── [Entidad Lógica]   Cursor      — posición lógica (columna)
            ├── [Entidad Lógica]   Conecta4    — estado, reglas, turnos, ganador
            ├── [Entidad Gráfica]  Tablero     — dibuja la cuadrícula 7×6
            ├── [Entidad Gráfica]  FichaX      — ficha Jugador 1 (reutilizada)
            └── [Entidad Gráfica]  FichaO      — ficha Jugador 2 (reutilizada)

Controles:
  ← →        → mover cursor (columna)
  ENTER      → soltar ficha
  R          → reiniciar partida (estadísticas persisten)
  ESC/Cerrar → salir
"""

import math
import sys
import pygame

# ═══════════════════════════════════════════════════════════════════
#  ENTIDADES GRÁFICAS  —
#  Solo se añade FichaCirculo para el estilo clásico del Conecta 4
# ═══════════════════════════════════════════════════════════════════


class EntidadGrafica:
    """
    Clase base para todas las entidades gráficas.
    ── REUTILIZADA DEL TRABAJO 01 SIN MODIFICACIONES ──
    """

    def __init__(self, x, y, e):
        self.x = x
        self.y = y
        self.e = e
        self.alfa = 0
        self.color = (255, 255, 255)

    def setColor(self, color):
        self.color = color

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def setEscala(self, e):
        self.e = e

    def render(self, pantalla):
        raise NotImplementedError


class FichaCirculo(EntidadGrafica):
    """
    Entidad Gráfica: disco sólido estilo clásico Conecta 4.
    ── NUEVA para Trabajo 02 ──
    Reemplaza FichaX y FichaO: ambos jugadores usan círculo relleno.
    J1 = rojo, J2 = amarillo (igual que el juego físico original).
    Incluye brillo superior para dar sensación de volumen (3D sutil).
    Animación de aparición: escala_aparicion crece de 0 a 1.
    """

    def __init__(self, x, y, e):
        super().__init__(x, y, e)
        self.escala_aparicion = 1.0

    def render(self, pantalla):
        e = self.e
        escala = max(0.01, self.escala_aparicion)
        tam_celda = 3 * e
        tam = int(tam_celda * escala)
        if tam < 3:
            return

        lienzo = pygame.Surface((tam_celda, tam_celda), pygame.SRCALPHA)

        cx = tam_celda // 2
        cy = tam_celda // 2
        radio = int(e * 1.05)

        # Sombra suave
        color_sombra = tuple(max(0, c - 80) for c in self.color)
        pygame.draw.circle(lienzo, (*color_sombra, 120), (cx + 2, cy + 3), radio)

        # Disco principal relleno
        pygame.draw.circle(lienzo, self.color, (cx, cy), radio)

        # Borde oscuro
        color_borde = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.circle(lienzo, color_borde, (cx, cy), radio, 2)

        # Brillo superior (reflejo pequeño blanco translúcido)
        brillo_r = max(3, radio // 3)
        brillo_cx = cx - radio // 4
        brillo_cy = cy - radio // 3
        pygame.draw.circle(lienzo, (255, 255, 255, 70), (brillo_cx, brillo_cy), brillo_r)

        # Aplicar escala de aparición (efecto "crecimiento desde cero")
        if escala < 1.0:
            lienzo_escalado = pygame.transform.scale(lienzo, (tam, tam))
            destino = pygame.Surface((tam_celda, tam_celda), pygame.SRCALPHA)
            offset = (tam_celda - tam) // 2
            destino.blit(lienzo_escalado, (offset, offset))
            lienzo = destino

        rotado = pygame.transform.rotate(lienzo, self.alfa)
        rect = rotado.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotado, rect)


# Alias para mantener compatibilidad con la arquitectura (mismo nombre de clase en la escena)
FichaX = FichaCirculo
FichaO = FichaCirculo


class Tablero(EntidadGrafica):
    """
    Entidad Gráfica: cuadrícula del Conecta 4.
    ── ADAPTADA DEL TRABAJO 01 ──
    Cambios: ahora soporta COLS x FILAS configurables (7×6 por defecto).
    Estética: fondo azul oscuro clásico del Conecta 4, huecos vacíos visibles.
    """

    GROSOR_MARCO = 4

    def __init__(self, x, y, e, cols=7, filas=6):
        super().__init__(x, y, e)
        self.cols = cols
        self.filas = filas
        self.color_tablero = (20, 60, 160)      # azul clásico Conecta 4
        self.color_hueco = (12, 12, 30)         # hueco vacío oscuro
        self.color_marco = (10, 40, 130)
        self.color_ganador = (240, 220, 50)
        self.celdas_ganadoras = []

    def set_celdas_ganadoras(self, celdas):
        self.celdas_ganadoras = celdas if celdas else []

    def render(self, pantalla):
        e = self.e
        ancho = self.cols * 3 * e
        alto = self.filas * 3 * e

        lienzo = pygame.Surface((ancho + 8, alto + 8), pygame.SRCALPHA)

        # Fondo azul del tablero
        pygame.draw.rect(lienzo, self.color_tablero, (4, 4, ancho, alto), border_radius=8)

        # Huecos circulares para cada celda
        for fila in range(self.filas):
            for col in range(self.cols):
                cx = 4 + col * 3 * e + (3 * e) // 2
                cy = 4 + fila * 3 * e + (3 * e) // 2
                radio = int(e * 1.1)

                # Resaltar celda ganadora
                if (fila, col) in self.celdas_ganadoras:
                    pygame.draw.circle(lienzo, (*self.color_ganador, 80), (cx, cy), radio + 4)

                pygame.draw.circle(lienzo, self.color_hueco, (cx, cy), radio)
                pygame.draw.circle(lienzo, (30, 30, 60), (cx, cy), radio, 2)

        # Marco exterior
        pygame.draw.rect(
            lienzo,
            self.color_marco,
            (0, 0, ancho + 8, alto + 8),
            self.GROSOR_MARCO,
            border_radius=10,
        )

        rotado = pygame.transform.rotate(lienzo, self.alfa)
        rect = rotado.get_rect(topleft=(self.x - 4, self.y - 4))
        pantalla.blit(rotado, rect)


# ═══════════════════════════════════════════════════════════════════
#  ENTIDADES LÓGICAS
# ═══════════════════════════════════════════════════════════════════


class Cursor:
    """
    Entidad Lógica: posición de selección del jugador.
    ── ADAPTADA DEL TRABAJO 01 ──
    Cambio clave: en Conecta 4 el cursor solo se mueve HORIZONTAL (columnas).
    No hay movimiento vertical porque la ficha CAE automáticamente.
    """

    def __init__(self, columna, max_columna):
        self.columna = columna
        self.max_columna = max_columna
        self.turno = 1
        self._pulso = 0.0
        self._pulso_vel = 0.05

    # ── Movimiento solo horizontal ───────────────────────────────
    def moverIzquierda(self):
        if self.columna > 0:
            self.columna -= 1

    def moverDerecha(self):
        if self.columna < self.max_columna - 1:
            self.columna += 1

    def getColumna(self):
        return self.columna

    def setTurno(self, turno):
        self.turno = turno

    def update(self):
        self._pulso += self._pulso_vel

    def render(self, pantalla, x, y, e):
        """
        Dibuja el cursor como flecha apuntando hacia abajo encima de la columna.
        ── Adaptación visual para Conecta 4 ──
        """
        COLOR_J1 = (220, 80, 80)
        COLOR_J2 = (240, 200, 50)
        color = COLOR_J1 if self.turno == 1 else COLOR_J2

        alpha = int(180 + 60 * math.sin(self._pulso))
        r, g, b = color
        color_a = (r, g, b, alpha)

        tam = 3 * e
        lienzo = pygame.Surface((tam, int(e * 1.5)), pygame.SRCALPHA)

        # Flecha triangular apuntando hacia abajo
        cx = tam // 2
        punta_y = int(e * 1.2)
        base_y = int(e * 0.1)
        mitad = int(e * 0.7)

        puntos = [
            (cx, punta_y),
            (cx - mitad, base_y),
            (cx + mitad, base_y),
        ]
        pygame.draw.polygon(lienzo, color_a, puntos)
        pygame.draw.polygon(lienzo, (255, 255, 255, 80), puntos, 2)

        pantalla.blit(lienzo, (x, y))


class Conecta4:
    """
    Entidad Lógica central: estado y reglas del Conecta 4.
    ── REEMPLAZA a TresEnRaya (misma interfaz pública, nueva lógica) ──

    Diferencias clave respecto a TresEnRaya:
      - Tablero 7 × 6 (en lugar de 3 × 3)
      - jugar(columna) en lugar de jugar(fila, columna) — la fila es calculada
      - La ficha CAE a la posición libre más baja (gravedad)
      - Victoria: 4 fichas consecutivas (no 3)
      - Detecta diagonal ascendente y descendente
    """

    VACIO = 0
    FICHA_J1 = 1
    FICHA_J2 = 2

    COLS = 7
    FILAS = 6

    def __init__(self):
        self._inicializar_estado()
        self.victorias_j1 = 0
        self.victorias_j2 = 0
        self.empates = 0
        self.partidas = 0

    def _inicializar_estado(self):
        self.matriz = [
            [self.VACIO] * self.COLS for _ in range(self.FILAS)
        ]
        self.turno = self.FICHA_J1
        self.ganador = self.VACIO
        self.celdas_ganadoras = []

    # ── Accesores ────────────────────────────────────────────────
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
            "victorias_j1": self.victorias_j1,
            "victorias_j2": self.victorias_j2,
            "empates": self.empates,
        }

    def columnaDisponible(self, col):
        """Retorna True si la columna todavía tiene espacio."""
        return self.matriz[0][col] == self.VACIO

    # ── Jugada ──────────────────────────────────────────────────
    def jugar(self, columna):
        """
        Intenta colocar la ficha del turno en la columna dada.
        La ficha CAE automáticamente a la fila más baja disponible.
        Retorna la fila donde cayó, o -1 si la jugada no fue válida.
        """
        if self.ganador != self.VACIO or self.hayEmpate():
            return -1
        if not (0 <= columna < self.COLS):
            return -1
        if not self.columnaDisponible(columna):
            return -1

        # ── CAÍDA DE FICHA: busca la fila libre más baja ────────
        fila_destino = -1
        for fila in range(self.FILAS - 1, -1, -1):
            if self.matriz[fila][columna] == self.VACIO:
                fila_destino = fila
                break

        self.matriz[fila_destino][columna] = self.turno
        self._verificarGanador(fila_destino, columna)

        if self.ganador != self.VACIO:
            self.partidas += 1
            if self.ganador == self.FICHA_J1:
                self.victorias_j1 += 1
            else:
                self.victorias_j2 += 1
        elif self.hayEmpate():
            self.partidas += 1
            self.empates += 1
        else:
            self.turno = self.FICHA_J2 if self.turno == self.FICHA_J1 else self.FICHA_J1

        return fila_destino

    # ── Verificación de victoria ─────────────────────────────────
    def _verificarGanador(self, fila, col):
        """
        Verifica las 4 direcciones posibles desde la ficha recién colocada.
        Esto es más eficiente que revisar todo el tablero en cada jugada.
        """
        ficha = self.matriz[fila][col]
        direcciones = [
            (0, 1),   # horizontal →
            (1, 0),   # vertical ↓
            (1, 1),   # diagonal ↘
            (1, -1),  # diagonal ↙
        ]

        for df, dc in direcciones:
            celdas = self._contarEnDireccion(fila, col, df, dc, ficha)
            if len(celdas) >= 4:
                self.ganador = ficha
                self.celdas_ganadoras = celdas[:4]
                return

    def _contarEnDireccion(self, fila, col, df, dc, ficha):
        """
        Cuenta fichas consecutivas en ambos sentidos de una dirección.
        Retorna la lista de celdas consecutivas encontradas.
        """
        celdas = [(fila, col)]

        # Sentido positivo
        f, c = fila + df, col + dc
        while 0 <= f < self.FILAS and 0 <= c < self.COLS and self.matriz[f][c] == ficha:
            celdas.append((f, c))
            f += df
            c += dc

        # Sentido negativo
        f, c = fila - df, col - dc
        while 0 <= f < self.FILAS and 0 <= c < self.COLS and self.matriz[f][c] == ficha:
            celdas.insert(0, (f, c))
            f -= df
            c -= dc

        return celdas

    # ── Empate ──────────────────────────────────────────────────
    def hayEmpate(self):
        if self.ganador != self.VACIO:
            return False
        return all(self.matriz[0][c] != self.VACIO for c in range(self.COLS))

    # ── Reinicio ────────────────────────────────────────────────
    def reiniciar(self):
        self._inicializar_estado()


# ═══════════════════════════════════════════════════════════════════
#  ESCENA PRINCIPAL
#  Misma estructura: Input → Update → Render
#  Cambios: coordina las nuevas entidades (Conecta4, Tablero 7×6)
# ═══════════════════════════════════════════════════════════════════


class EscenaConecta4:
    """
    Coordinadora de todas las entidades del Conecta 4.
    Misma estructura que EscenaTresEnRaya del Trabajo 01.

    ── Reutilizado: ──
      Flujo Input → Update → Render
      Animaciones de aparición de fichas
      Parpadeo del mensaje final
      Puente lógica → gráfica (celdas_ganadoras)

    ── Adaptado: ──
      Input: solo teclas ← → (sin arriba/abajo)
      Render: tablero 7×6, fichas circulares, panel lateral
    """

    COLOR_J1 = (220, 80, 80)    # rojo  — jugador 1
    COLOR_J2 = (240, 200, 50)   # amarillo — jugador 2
    COLOR_UI = (190, 190, 210)

    def __init__(self):
        # TAMAÑO ARREGLADO: self.e ajustado a 28 para que quepa en pantalla
        self.e = 28  

        # Márgenes arreglados para centrar el contenido
        margen_x = 40
        margen_y = 60

        self.tablero = Tablero(margen_x, margen_y, self.e,
                               cols=Conecta4.COLS, filas=Conecta4.FILAS)

        self.cursor = Cursor(3, Conecta4.COLS)
        self.juego = Conecta4()

        self._escala_fichas: dict = {}
        self._parpadeo = 0.0
        self._parpadeo_vel = 0.06

    # ════════════════════════════════════════════════════════════
    #  INPUT — igual que Trabajo 01, pero solo ← →
    # ════════════════════════════════════════════════════════════
    def input(self, evento):
        if evento.type != pygame.KEYDOWN:
            return
        if self.hayGanador() or self.hayEmpate():
            return

        if evento.key == pygame.K_LEFT:
            self.cursor.moverIzquierda()
        elif evento.key == pygame.K_RIGHT:
            self.cursor.moverDerecha()

        elif evento.key == pygame.K_RETURN:
            col = self.cursor.getColumna()
            fila_destino = self.juego.jugar(col)
            if fila_destino >= 0:
                self._escala_fichas[(fila_destino, col)] = 0.05
                self.cursor.setTurno(self.juego.getTurno())

    # ════════════════════════════════════════════════════════════
    #  UPDATE — igual que Trabajo 01
    # ════════════════════════════════════════════════════════════
    def update(self):
        self.cursor.update()

        terminadas = []
        for clave, escala in self._escala_fichas.items():
            nueva = min(1.0, escala + 0.08)
            self._escala_fichas[clave] = nueva
            if nueva >= 1.0:
                terminadas.append(clave)
        for k in terminadas:
            del self._escala_fichas[k]

        self.tablero.set_celdas_ganadoras(self.juego.getCeldasGanadoras())

        if self.hayGanador() or self.hayEmpate():
            self._parpadeo += self._parpadeo_vel

    # ════════════════════════════════════════════════════════════
    #  RENDER — adaptado a 7×6
    # ════════════════════════════════════════════════════════════
    def render(self, pantalla):
        # 1. Tablero
        self.tablero.render(pantalla)

        # 2. Cursor (flecha sobre la columna seleccionada)
        if not self.hayGanador() and not self.hayEmpate():
            cx = self.tablero.x + self.cursor.getColumna() * 3 * self.e
            cy = self.tablero.y - int(self.e * 1.6)
            self.cursor.render(pantalla, cx, cy, self.e)

        # 3. Fichas encima de los huecos del tablero
        matriz = self.juego.getMatriz()
        for fila in range(Conecta4.FILAS):
            for col in range(Conecta4.COLS):
                x = self.tablero.x + col * 3 * self.e
                y = self.tablero.y + fila * 3 * self.e
                escala = self._escala_fichas.get((fila, col), 1.0)

                if matriz[fila][col] == Conecta4.FICHA_J1:
                    ficha = FichaX(x, y, self.e)
                    ficha.setColor(self.COLOR_J1)
                    ficha.escala_aparicion = escala
                    ficha.render(pantalla)

                elif matriz[fila][col] == Conecta4.FICHA_J2:
                    ficha = FichaO(x, y, self.e)
                    ficha.setColor(self.COLOR_J2)
                    ficha.escala_aparicion = escala
                    ficha.render(pantalla)

        # 4. Panel de información
        self._renderPanel(pantalla)

    # ────────────────────────────────────────────────────────────
    def _renderPanel(self, pantalla):
        e = self.e
        panel_x = self.tablero.x + Conecta4.COLS * 3 * e + 30
        fuente = pygame.font.SysFont("consolas", 22, bold=True)
        fuente_sm = pygame.font.SysFont("consolas", 17)
        fuente_xs = pygame.font.SysFont("consolas", 15)

        # ── Turno actual ─────────────────────────────────────────
        if not self.hayGanador() and not self.hayEmpate():
            turno = self.juego.getTurno()
            color_t = self.COLOR_J1 if turno == Conecta4.FICHA_J1 else self.COLOR_J2
            nombre = "Turno: J1" if turno == Conecta4.FICHA_J1 else "Turno: J2"
            lbl = fuente.render(nombre, True, color_t)
            pantalla.blit(lbl, (panel_x, 80))

            # Miniatura de ficha del turno
            if turno == Conecta4.FICHA_J1:
                fx = FichaX(panel_x, 112, e // 2)
                fx.setColor(self.COLOR_J1)
                fx.render(pantalla)
            else:
                fo = FichaO(panel_x, 112, e // 2)
                fo.setColor(self.COLOR_J2)
                fo.render(pantalla)

        # ── Estadísticas ─────────────────────────────────────────
        y_est = 210
        lbl2 = fuente.render("Estadísticas", True, self.COLOR_UI)
        pantalla.blit(lbl2, (panel_x, y_est))
        y_est += 28

        est = self.juego.getEstadisticas()
        lineas = [
            (f"Partidas: {est['partidas']}", self.COLOR_UI),
            (f"J1 gana: {est['victorias_j1']}", self.COLOR_J1),
            (f"J2 gana: {est['victorias_j2']}", self.COLOR_J2),
            (f"Empates: {est['empates']}", (180, 230, 180)),
        ]
        for texto, color in lineas:
            pantalla.blit(fuente_sm.render(texto, True, color), (panel_x, y_est))
            y_est += 24

        # ── Leyenda de jugadores ──────────────────────────────────
        y_ley = y_est + 20
        pantalla.blit(fuente_sm.render("Jugadores:", True, self.COLOR_UI), (panel_x, y_ley))
        y_ley += 24
        pantalla.blit(fuente_sm.render("J1 = O (rojo)", True, self.COLOR_J1), (panel_x, y_ley))
        y_ley += 22
        pantalla.blit(fuente_sm.render("J2 = O (amarillo)", True, self.COLOR_J2), (panel_x, y_ley))

        # ── Mensaje de fin ───────────────────────────────────────
        ganador = self.hayGanador()
        if ganador == Conecta4.FICHA_J1:
            self._dibujarMensajeFin(pantalla, "¡GANA J1!", self.COLOR_J1, panel_x)
        elif ganador == Conecta4.FICHA_J2:
            self._dibujarMensajeFin(pantalla, "¡GANA J2!", self.COLOR_J2, panel_x)
        elif self.hayEmpate():
            self._dibujarMensajeFin(pantalla, "EMPATE", (180, 230, 180), panel_x)

        # ── Controles ────────────────────────────────────────────
        ayuda_y = pantalla.get_height() - 36
        ayuda = fuente_xs.render(
            "← →: columna  |  ENTER: soltar ficha  |  R: reiniciar  |  ESC: salir",
            True,
            (110, 110, 130),
        )
        pantalla.blit(ayuda, (30, ayuda_y))

    def _dibujarMensajeFin(self, pantalla, texto, color, panel_x):
      """Mensaje de fin de juego con parpadeo suave."""
      alpha = int(140 + 100 * math.sin(self._parpadeo))
      fuente_grande = pygame.font.SysFont("consolas", 46, bold=True)
      fuente_sm = pygame.font.SysFont("consolas", 20)

      sup = fuente_grande.render(texto, True, color)
      sup.set_alpha(alpha)
      pantalla.blit(sup, (panel_x, 460)) 

      hint = fuente_sm.render("Presiona  R  para", True, (170, 170, 170))
      pantalla.blit(hint, (panel_x, 515)) 
    
      hint2 = fuente_sm.render("reiniciar", True, (170, 170, 170))
      pantalla.blit(hint2, (panel_x + 20, 536)) 
        

    # ════════════════════════════════════════════════════════════
    #  Consultas de estado
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
        self.cursor = Cursor(3, Conecta4.COLS)
        self._escala_fichas = {}
        self._parpadeo = 0.0
        self.tablero.set_celdas_ganadoras([])


# ═══════════════════════════════════════════════════════════════════
#  GAME LOOP — 
# ═══════════════════════════════════════════════════════════════════


def main():
    pygame.init()

    ANCHO = 980
    ALTO  = 660
    FPS   = 60
    COLOR_FONDO = (10, 10, 24)

    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Conecta 4  —  Trabajo 02  |  Reutilización de Arquitectura")

    clock = pygame.time.Clock()

    # La escena es el organismo que el Game Loop mantiene vivo
    escena = EscenaConecta4()

    # ── GAME LOOP (mismo patrón que Trabajo 01) ──────────────────
    while True:
        # ── INPUT ────────────────────────────────────────────────
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

        # ── UPDATE ───────────────────────────────────────────────
        escena.update()

        # ── RENDER ───────────────────────────────────────────────
        pantalla.fill(COLOR_FONDO)
        escena.render(pantalla)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()