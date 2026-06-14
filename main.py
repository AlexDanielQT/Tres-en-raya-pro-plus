import pygame
import sys

# =============================================================================
# CAPA GRAFICA — Entidades visuales
# Responsabilidad: solo dibujar. No conocen reglas del juego ni estadisticas.
# =============================================================================

class Base:
    """Clase base para todas las entidades graficas.
    Agrupa los atributos visuales comunes: posicion, escala, color y rotacion.
    """

    def __init__(self, x, y, e):
        self.x = x
        self.y = y
        self.e = e
        self.color = (255, 255, 255)
        self.alfa = 0

    def setColor(self, color):
        self.color = color

    def setX(self, x):
        self.x = x

    def setY(self, y):
        self.y = y

    def setXY(self, x, y):
        self.x = x
        self.y = y

    def setEscala(self, e):
        self.e = e


class X(Base):
    """Entidad grafica de la ficha X.
    PENDIENTE: mejorar visualmente (grosor, colores, bordes, estilo).
    """

    def __init__(self, x, y, e):
        super().__init__(x, y, e)

    def render(self, pantalla):
        e = self.e
        lienzo = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)

        pygame.draw.line(lienzo, self.color, (0, 0), (3 * e, 3 * e), 1)
        pygame.draw.line(lienzo, self.color, (3 * e, 0), (0, 3 * e), 1)

        rotacion = pygame.transform.rotate(lienzo, self.alfa)
        traslacion = rotacion.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotacion, traslacion)


class O(Base):
    """Entidad grafica de la ficha O.
    PENDIENTE: mejorar visualmente (doble circulo, degradado simulado, detalles).
    """

    def __init__(self, x, y, e):
        super().__init__(x, y, e)

    def render(self, pantalla):
        e = self.e
        lienzo = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)

        pygame.draw.circle(lienzo, self.color, (3 * e // 2, 3 * e // 2), (3 * e // 2), 1)

        rotacion = pygame.transform.rotate(lienzo, self.alfa)
        traslacion = rotacion.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotacion, traslacion)


class Tablero(Base):
    """Entidad grafica del tablero.
    Recibe el tamanio del juego (n) para adaptarse a tableros N x N.
    PENDIENTE: mejorar visualmente (colores, marcos, efectos).
    """

    def __init__(self, x, y, e, n=3):
        super().__init__(x, y, e)
        # n: numero de celdas por lado. Se usa para dibujar la grilla correcta.
        self.n = n

    def render(self, pantalla):
        e = self.e
        n = self.n
        total = n * 3 * e
        lienzo = pygame.Surface((total, total), pygame.SRCALPHA)

        # Lineas verticales internas
        for i in range(1, n):
            pygame.draw.line(lienzo, self.color, (i * 3 * e, 0), (i * 3 * e, total), 1)

        # Lineas horizontales internas
        for i in range(1, n):
            pygame.draw.line(lienzo, self.color, (0, i * 3 * e), (total, i * 3 * e), 1)

        rotacion = pygame.transform.rotate(lienzo, self.alfa)
        traslacion = rotacion.get_rect(topleft=(self.x, self.y))
        pantalla.blit(rotacion, traslacion)


class Cursor:
    """Entidad de control y navegacion.
    Ahora soporta wrap-around: al llegar a un borde, aparece en el lado opuesto.
    Tambien recibe el tamanio del tablero (n) para adaptarse a cualquier N x N.
    PENDIENTE: mejorar visualmente (color segun turno, borde atractivo, efecto pulsante).
    """

    def __init__(self, fila, columna, n=3):
        self.fila = fila
        self.columna = columna
        # n: numero de celdas por lado. Define el rango valido de movimiento.
        self.n = n

    # ------------------------------------------------------------------
    # NUEVA FUNCIONALIDAD: wrap-around
    # Antes: if self.fila > 0: self.fila -= 1   (se bloqueaba en el borde)
    # Ahora: self.fila = (self.fila - 1) % self.n  (vuelve al lado opuesto)
    # El operador % con valores negativos en Python siempre devuelve positivo,
    # por eso -1 % 3 = 2, que es exactamente el ultimo indice del tablero 3x3.
    # ------------------------------------------------------------------

    def moverArriba(self):
        self.fila = (self.fila - 1) % self.n

    def moverAbajo(self):
        self.fila = (self.fila + 1) % self.n

    def moverIzquierda(self):
        self.columna = (self.columna - 1) % self.n

    def moverDerecha(self):
        self.columna = (self.columna + 1) % self.n

    def getFila(self):
        return self.fila

    def getColumna(self):
        return self.columna

    def getPosicion(self):
        return (self.fila, self.columna)

    def render(self, pantalla, x, y, e, color):
        """
        PENDIENTE: reemplazar con un diseno mas atractivo.
        Recibe 'color' desde la escena para que en el futuro
        la escena pueda pasarle el color del jugador actual.
        """
        lienzo = pygame.Surface((3 * e, 3 * e), pygame.SRCALPHA)
        pygame.draw.rect(lienzo, color, (e // 2, e // 2, 2 * e, 2 * e), 1)

        rotacion = pygame.transform.rotate(lienzo, 0)
        traslacion = rotacion.get_rect(topleft=(x, y))
        pantalla.blit(rotacion, traslacion)


# =============================================================================
# CAPA LOGICA — Estado del juego
# Responsabilidad: reglas, estado, validaciones. No sabe de pixeles ni de pygame.
# =============================================================================

class Estadisticas:
    """Lleva el conteo de victorias y empates a lo largo de multiples partidas.
    Es independiente de TresEnRaya: persiste cuando el juego se reinicia.

    Separada en su propia clase para respetar el principio de responsabilidad
    unica: TresEnRaya maneja UNA partida; Estadisticas maneja el historial.
    """

    def __init__(self):
        self.victorias = {
            TresEnRaya.FICHA_X: 0,
            TresEnRaya.FICHA_O: 0,
        }
        self.empates = 0
        # Historial: lista de strings describiendo cada resultado
        self.historial = []

    def registrarVictoria(self, ficha):
        """Registra una victoria para la ficha indicada (FICHA_X o FICHA_O)."""
        self.victorias[ficha] += 1
        nombre = "X" if ficha == TresEnRaya.FICHA_X else "O"
        self.historial.append(f"Victoria de {nombre}")

    def registrarEmpate(self):
        """Registra un empate."""
        self.empates += 1
        self.historial.append("Empate")

    def getVictorias(self, ficha):
        return self.victorias[ficha]

    def getEmpates(self):
        return self.empates

    def getHistorial(self):
        """Devuelve una copia del historial para que nadie lo modifique externamente."""
        return list(self.historial)

    def getResumen(self):
        """Devuelve un diccionario con el resumen actual. Util para el render."""
        return {
            "victorias_x": self.victorias[TresEnRaya.FICHA_X],
            "victorias_o": self.victorias[TresEnRaya.FICHA_O],
            "empates": self.empates,
            "total_partidas": len(self.historial),
        }


class HistorialJugadas:
    """Registra cada jugada de la partida actual como un objeto con datos utiles.

    Separado de TresEnRaya para no mezclar responsabilidades: el juego aplica
    reglas, el historial simplemente guarda lo que paso y quien lo hizo.
    Se limpia al reiniciar la partida (ver EscenaTresEnRaya.reiniciar).
    """

    def __init__(self):
        self.jugadas = []

    def registrar(self, ficha, fila, columna):
        """Guarda una jugada con su turno de numero, quien jugo y donde."""
        jugada = {
            "turno": len(self.jugadas) + 1,
            "ficha": "X" if ficha == TresEnRaya.FICHA_X else "O",
            "fila": fila,
            "columna": columna,
        }
        self.jugadas.append(jugada)

    def getJugadas(self):
        """Devuelve una copia de la lista de jugadas."""
        return list(self.jugadas)

    def getUltimaJugada(self):
        """Devuelve la jugada mas reciente, o None si no hay ninguna."""
        if self.jugadas:
            return self.jugadas[-1]
        return None

    def limpiar(self):
        """Vacia el historial al comenzar una nueva partida."""
        self.jugadas = []


class TresEnRaya:
    """Logica pura del juego. Maneja UNA partida.

    NUEVO: acepta parametros de configuracion:
      - n:          tamanio del tablero (n x n). Por defecto 3.
      - fichas_para_ganar: cuantas fichas consecutivas se necesitan para ganar.
                           Por defecto igual a n (comportamiento original).

    Esto permite crear tableros 4x4, 5x5, etc., sin modificar el resto del codigo.
    """

    VACIO  = 0
    FICHA_X = 1
    FICHA_O = 2

    def __init__(self, n=3, fichas_para_ganar=None):
        self.n = n
        # Si no se especifica, se necesitan n fichas en linea para ganar (comportamiento clasico).
        self.fichas_para_ganar = fichas_para_ganar if fichas_para_ganar is not None else n

        self.matriz = [[self.VACIO] * n for _ in range(n)]
        self.turno  = self.FICHA_X
        self.ganador = self.VACIO

    # ------------------------------------------------------------------
    # Getters — la escena y otras capas los usan para leer estado
    # ------------------------------------------------------------------

    def getMatriz(self):
        return self.matriz

    def getTurno(self):
        return self.turno

    def getGanador(self):
        return self.ganador

    def getTamanio(self):
        return self.n

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def jugar(self, fila, columna):
        """Intenta colocar la ficha del turno actual en (fila, columna).
        Devuelve True si la jugada fue valida, False si la casilla estaba ocupada.
        """
        if self.ganador != self.VACIO:
            return False

        if self.hayEmpate():
            return False

        if self.matriz[fila][columna] != self.VACIO:
            return False

        turno_actual = self.turno
        self.matriz[fila][columna] = turno_actual

        self.verificarGanador()

        # Solo cambia el turno si la partida continua
        if self.ganador == self.VACIO:
            self._alternarTurno()

        # Devuelve True junto con el turno que acaba de jugar
        # para que la escena pueda registrar la jugada correctamente
        return True

    def _alternarTurno(self):
        """Cambia el turno al otro jugador."""
        if self.turno == self.FICHA_X:
            self.turno = self.FICHA_O
        else:
            self.turno = self.FICHA_X

    def reiniciar(self):
        """Resetea el estado de la partida actual. Las estadisticas NO se tocan aqui."""
        self.matriz  = [[self.VACIO] * self.n for _ in range(self.n)]
        self.turno   = self.FICHA_X
        self.ganador = self.VACIO

    # ------------------------------------------------------------------
    # Verificacion del estado del juego
    # ------------------------------------------------------------------

    def verificarGanador(self):
        """Detecta si hay un ganador en la partida actual.

        Generalizado para tableros N x N y M fichas para ganar.
        Revisa filas, columnas y ambas diagonales buscando M fichas
        consecutivas del mismo jugador.
        """
        m   = self.matriz
        n   = self.n
        fxg = self.fichas_para_ganar

        # Filas
        for fila in range(n):
            ganador = self._buscarConsecutivos(m[fila])
            if ganador:
                self.ganador = ganador
                return

        # Columnas
        for col in range(n):
            columna = [m[fila][col] for fila in range(n)]
            ganador = self._buscarConsecutivos(columna)
            if ganador:
                self.ganador = ganador
                return

        # Diagonal principal (arriba-izquierda a abajo-derecha)
        diagonal_principal = [m[i][i] for i in range(n)]
        ganador = self._buscarConsecutivos(diagonal_principal)
        if ganador:
            self.ganador = ganador
            return

        # Diagonal secundaria (arriba-derecha a abajo-izquierda)
        diagonal_secundaria = [m[i][n - 1 - i] for i in range(n)]
        ganador = self._buscarConsecutivos(diagonal_secundaria)
        if ganador:
            self.ganador = ganador
            return

    def _buscarConsecutivos(self, linea):
        """Busca 'fichas_para_ganar' valores iguales y no vacios consecutivos en una lista.

        Devuelve el valor ganador si lo encuentra, o None si no hay ganador en esa linea.

        Ejemplo con fichas_para_ganar=3:
          [X, X, X]    -> devuelve X
          [X, X, O]    -> devuelve None
          [0, X, X, X] -> devuelve X  (funciona para tableros mayores a 3x3)
        """
        consecutivos = 1
        for i in range(1, len(linea)):
            if linea[i] != self.VACIO and linea[i] == linea[i - 1]:
                consecutivos += 1
                if consecutivos >= self.fichas_para_ganar:
                    return linea[i]
            else:
                consecutivos = 1
        return None

    def hayEmpate(self):
        """Devuelve True si el tablero esta lleno y no hay ganador."""
        if self.ganador != self.VACIO:
            return False

        for fila in self.matriz:
            for casilla in fila:
                if casilla == self.VACIO:
                    return False

        return True


# =============================================================================
# CAPA DE ESCENA — Orquestador
# Responsabilidad: coordinar input, update y render. Conecta logica y grafica.
# No aplica reglas del juego (eso es de TresEnRaya).
# No dibuja primitivas (eso es de las entidades graficas).
# =============================================================================

class EscenaTresEnRaya:
    """Orquestador principal. Implementa el contrato input / update / render.

    Maneja:
      - La instancia del juego (TresEnRaya)
      - Las estadisticas entre partidas (Estadisticas)
      - El historial de jugadas de la partida actual (HistorialJugadas)
      - Las entidades graficas (Tablero, Cursor, fichas de turno)
    """

    def __init__(self, n=3, fichas_para_ganar=None):
        self.e = 30
        self.n = n

        # Animacion de los indicadores de turno
        self.incXTurno = 0.5
        self.incYTurno = 0.5

        # Entidades graficas — reciben n para adaptarse al tamanio del tablero
        self.tablero = Tablero(10, 10, self.e, n)
        self.tablero.setColor((255, 255, 255))

        self.cursor = Cursor(n // 2, n // 2, n)

        # Indicadores de turno (posiciones fijas en la pantalla)
        self.xTurno = X(320, 50, self.e // 2)
        self.xTurno.setColor((255, 0, 0))

        self.oTurno = O(420, 50, self.e // 2)
        self.oTurno.setColor((0, 255, 255))

        # Logica
        self.juego = TresEnRaya(n, fichas_para_ganar)

        # Estadisticas y historial — instanciados aqui para que
        # la escena los controle (sabe cuando registrar y cuando limpiar)
        self.estadisticas   = Estadisticas()
        self.historialJugadas = HistorialJugadas()

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def input(self, evento):
        """Procesa eventos de teclado y los traduce en acciones logicas."""
        if evento.type != pygame.KEYDOWN:
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
            self._intentarJugar()

        # NUEVA TECLA: R para reiniciar la partida (manteniendo estadisticas)
        elif evento.key == pygame.K_r:
            self.reiniciar()

    def _intentarJugar(self):
        """Intenta realizar una jugada y, si es valida, la registra en el historial."""
        fila    = self.cursor.getFila()
        columna = self.cursor.getColumna()

        # Guardamos el turno ANTES de jugar, porque jugar() lo puede cambiar
        turno_actual = self.juego.getTurno()

        jugada_valida = self.juego.jugar(fila, columna)

        if jugada_valida:
            # Registramos quien jugo y donde
            self.historialJugadas.registrar(turno_actual, fila, columna)

            # Si la jugada termino la partida, actualizamos estadisticas
            ganador = self.juego.getGanador()
            if ganador != TresEnRaya.VACIO:
                self.estadisticas.registrarVictoria(ganador)

            elif self.juego.hayEmpate():
                self.estadisticas.registrarEmpate()

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self):
        """Actualiza el estado animado de la escena cada frame."""
        if self.juego.getGanador() != TresEnRaya.VACIO:
            return

        if self.juego.hayEmpate():
            return

        # Anima el indicador del jugador cuyo turno es activo
        if self.juego.getTurno() == TresEnRaya.FICHA_X:
            if self.xTurno.e >= 0.5 * self.e or self.xTurno.e <= self.e // 4:
                self.incXTurno = -self.incXTurno
            self.xTurno.e += self.incXTurno
        else:
            if self.oTurno.e >= 0.5 * self.e or self.oTurno.e <= self.e // 4:
                self.incYTurno = -self.incYTurno
            self.oTurno.e += self.incYTurno

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(self, pantalla):
        """Dibuja todos los elementos de la escena."""
        self.tablero.render(pantalla)

        # Posicion del cursor en pixeles (segun su celda logica)
        x = self.tablero.x + self.cursor.getColumna() * 3 * self.e
        y = self.tablero.y + self.cursor.getFila()    * 3 * self.e

        # PENDIENTE: pasar el color del jugador actual al cursor
        # Ejemplo: color = (255,0,0) si turno==X, (0,255,255) si turno==O
        self.cursor.render(pantalla, x, y, self.e, (255, 255, 0))

        # Dibuja las fichas segun la matriz logica
        matriz = self.juego.getMatriz()
        n = self.n

        for fila in range(n):
            for columna in range(n):
                cx = self.tablero.x + columna * 3 * self.e
                cy = self.tablero.y + fila    * 3 * self.e

                if matriz[fila][columna] == TresEnRaya.FICHA_X:
                    ficha = X(cx, cy, self.e)
                    ficha.setColor((255, 0, 0))
                    ficha.render(pantalla)

                elif matriz[fila][columna] == TresEnRaya.FICHA_O:
                    ficha = O(cx, cy, self.e)
                    ficha.setColor((0, 255, 255))
                    ficha.render(pantalla)

        # Indicadores de turno animados
        self.xTurno.render(pantalla)
        self.oTurno.render(pantalla)

        # PENDIENTE: renderizar las estadisticas en pantalla
        # self.estadisticas.getResumen() ya esta disponible con todos los datos

    # ------------------------------------------------------------------
    # Consultas de estado — usadas por el game loop o por otros sistemas
    # ------------------------------------------------------------------

    def hayGanador(self):
        return self.juego.getGanador()

    def hayEmpate(self):
        return self.juego.hayEmpate()

    def getEstadisticas(self):
        """Devuelve el resumen de estadisticas. Util para renderizarlo."""
        return self.estadisticas.getResumen()

    def getHistorialJugadas(self):
        """Devuelve las jugadas de la partida actual."""
        return self.historialJugadas.getJugadas()

    # ------------------------------------------------------------------
    # Reinicio
    # ------------------------------------------------------------------

    def reiniciar(self):
        """Reinicia la partida actual sin borrar las estadisticas acumuladas."""
        self.juego.reiniciar()

        # El cursor vuelve al centro del tablero
        self.cursor = Cursor(self.n // 2, self.n // 2, self.n)

        # El historial de jugadas se limpia porque es una partida nueva
        self.historialJugadas.limpiar()

        # Las animaciones vuelven a cero
        self.xTurno.alfa = 0
        self.oTurno.alfa = 0


# =============================================================================
# GAME LOOP
# =============================================================================

pygame.init()

ANCHO = 600
ALTO  = 400
pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("3 en Raya Pro+")

clock = pygame.time.Clock()

# Tablero 3x3 clasico. Para probar un tablero 4x4: EscenaTresEnRaya(n=4)
escena = EscenaTresEnRaya(n=3)

while True:
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        escena.input(evento)

    escena.update()

    pantalla.fill((0, 0, 0))

    escena.render(pantalla)

    pygame.display.flip()

    clock.tick(60)
