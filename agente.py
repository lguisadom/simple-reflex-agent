import pygame
import random
import csv
import time
import os
from datetime import datetime

TABLES_FOLDER = "tablas"
FILE_NAME = None  # Se establecerá dinámicamente

# --- Parámetros del entorno ---
ROWS, COLS = 11, 11  # Valores por defecto, se pueden cambiar desde el menú
CELL_SIZE = 50  # Se ajusta automáticamente según el tamaño del mapa
FPS = 60  # Aumentar FPS para animaciones más fluidas
#STEP_DELAY = 0.7
STEP_DELAY = 0.1

# --- Colores ---
WHITE = (230, 230, 230)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
RED = (255, 60, 60)
BLUE = (40, 100, 255)
TEXT = (20, 20, 20)

DENSITY = 0.3

# --- Funciones para manejo de tablas ---
def get_available_tables():
    """Detecta automáticamente todas las tablas CSV disponibles en la carpeta tablas/"""
    tables = []
    if not os.path.exists(TABLES_FOLDER):
        os.makedirs(TABLES_FOLDER, exist_ok=True)
        return tables
    
    for filename in os.listdir(TABLES_FOLDER):
        if filename.endswith('.csv'):
            tables.append(filename)
    
    return sorted(tables)

def get_table_description(filename):
    """Obtiene una descripción de la tabla basada en su nombre"""
    descriptions = {
        "percepcion-accion.csv": "Tabla Original - Comportamiento básico",
        "percepcion-accion2.csv": "Tabla Alternativa - Estrategia diferente",
        "conservador.csv": "Tabla Conservadora - Siempre gira a la derecha",
    }
    
    # Si no hay descripción específica, usar el nombre del archivo
    return descriptions.get(filename, f"Tabla Personalizada - {filename}")

def get_direction_arrow(orientation):
    """Devuelve la flecha direccional correspondiente a la orientación"""
    arrows = {
        'N': '↑',  # Norte
        'E': '→',  # Este
        'S': '↓',  # Sur
        'W': '←'   # Oeste
    }
    return arrows.get(orientation, '?')

# --- Mostrar menú de selección de tabla ---
def show_table_selection_menu(screen):
    font_title = pygame.font.SysFont("consolas", 28, bold=True)
    font_option = pygame.font.SysFont("consolas", 20)
    font_instruction = pygame.font.SysFont("consolas", 16)
    
    # Obtener tablas disponibles
    tables = get_available_tables()
    
    if not tables:
        # Si no hay tablas, mostrar mensaje de error
        screen.fill(WHITE)
        error_text = font_option.render("No se encontraron tablas CSV en la carpeta 'tablas/'", True, RED)
        error_rect = error_text.get_rect(center=(screen.get_width()//2, 200))
        screen.blit(error_text, error_rect)
        
        inst_text = font_instruction.render("Presiona ESC para salir", True, TEXT)
        inst_rect = inst_text.get_rect(center=(screen.get_width()//2, 250))
        screen.blit(inst_text, inst_rect)
        
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
        return None
    
    # Selección por defecto (primera opción)
    selected_index = 0
    
    # Loop principal
    running = True
    while running:
        # Limpiar pantalla
        screen.fill(WHITE)
        
        # Título
        title = font_title.render("SELECCIÓN DE TABLA DE REGLAS", True, TEXT)
        title_rect = title.get_rect(center=(screen.get_width()//2, 80))
        screen.blit(title, title_rect)
        
        # Mostrar opciones de tablas
        y_offset = 150
        for i, table in enumerate(tables):
            # Determinar color según si está seleccionada
            if i == selected_index:
                text_color = BLUE
                prefix = "► "
            else:
                text_color = TEXT
                prefix = "  "
            
            option_text = f"{prefix}{table}"
            option = font_option.render(option_text, True, text_color)
            option_rect = option.get_rect(center=(screen.get_width()//2, y_offset))
            screen.blit(option, option_rect)
            y_offset += 40
        
        # Instrucciones
        inst1 = font_instruction.render("Usa las flechas ↑↓ para navegar, ENTER para seleccionar", True, TEXT)
        inst2 = font_instruction.render("• ESC: Salir", True, TEXT)
        
        inst1_rect = inst1.get_rect(center=(screen.get_width()//2, y_offset + 20))
        inst2_rect = inst2.get_rect(center=(screen.get_width()//2, y_offset + 50))
        
        screen.blit(inst1, inst1_rect)
        screen.blit(inst2, inst2_rect)
        
        pygame.display.flip()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    return tables[selected_index]
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(tables)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(tables)

# --- Crear mapa ---
def create_map(rows, cols, density=DENSITY):
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            if r == 0 or r == rows - 1 or c == 0 or c == cols - 1:
                row.append(-1)
            else:
                row.append(1 if random.random() < density else 0)
        grid.append(row)
    return grid

# --- Cargar tabla percepción-acción ---
def load_table(filename):
    table = {}
    rule_index = {}  # <--- Nuevo diccionario para guardar número de regla
    filepath = os.path.join(TABLES_FOLDER, filename)
    with open(filepath, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        line_num = 0
        for row in reader:
            if not row or row[0].startswith('#'):
                continue
            line_num += 1
            piso, izq, cen, der, contacto, *acciones = [x.strip() for x in row]
            key = (piso, izq, cen, der, contacto)
            table[key] = acciones
            rule_index[key] = line_num  # <--- Guarda el número de regla
    return table, rule_index
    
# --- Clase Agente ---
class Agent:
    def __init__(self, grid):
        self.orient = random.choice(['N', 'E', 'S', 'W'])
        while True:
            r = random.randint(1, ROWS - 2)
            c = random.randint(1, COLS - 2)
            if grid[r][c] != -1:
                self.x, self.y = r, c
                break
        self.contact = '0'

    def rotate(self, delta):
        dirs = ['N', 'E', 'S', 'W']
        idx = dirs.index(self.orient)
        self.orient = dirs[(idx + delta) % 4]

    def forward(self, grid):
        moves = {'N': (-1, 0), 'E': (0, 1), 'S': (1, 0), 'W': (0, -1)}
        dx, dy = moves[self.orient]
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < ROWS and 0 <= ny < COLS and grid[nx][ny] != -1:
            self.x, self.y = nx, ny
            self.contact = '0'
        else:
            self.contact = '1'

# --- Percepción ---
def sense(grid, agent):
    piso = '1' if grid[agent.x][agent.y] == 1 else '0'
    contact = agent.contact

    offsets = {
        'N': [(-1, -1), (-1, 0), (-1, 1)],
        'E': [(-1, 1), (0, 1), (1, 1)],
        'S': [(1, 1), (1, 0), (1, -1)],
        'W': [(1, -1), (0, -1), (-1, -1)],
    }

    left, center, right = '.', '.', '.'
    for i, (dx, dy) in enumerate(offsets[agent.orient]):
        nx, ny = agent.x + dx, agent.y + dy
        if not (0 <= nx < ROWS and 0 <= ny < COLS):
            val = 'P'
        elif grid[nx][ny] == -1:
            val = 'P'
        elif grid[nx][ny] == 1:
            val = 'L'
        else:
            val = '.'
        if i == 0: left = val
        elif i == 1: center = val
        else: right = val
    return (piso, left, center, right, contact)

def decide(percep, tabla, indices):
    if percep in tabla:
        return tabla[percep], percep, indices[percep]
    # Si no hay coincidencia, devolvemos una acción por defecto y sin número
    return ['ROTAR+90', 'AVANZAR'], percep, None

# --- Ejecutar acción ---
def ejecutar(agent, grid, accion):
    if accion == 'AVANZAR':
        agent.forward(grid)
    elif accion == 'ROTAR+90':
        agent.rotate(-1)
    elif accion == 'ROTAR-90':
        agent.rotate(+1)

# --- Dibujar ---
def draw(screen, grid, agent, percep, acciones, iteracion, regla_idx=None, mode="step_by_step"):
    screen.fill(WHITE)

    # Dibujar mapa
    for r in range(ROWS):
        for c in range(COLS):
            val = grid[r][c]
            if val == -1:
                # Dibujar pared con efecto de rayas
                pygame.draw.rect(screen, GRAY, (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                
                # Dibujar rayas horizontales
                stripe_height = 3
                stripe_spacing = 6
                y_offset = 0
                
                while y_offset < CELL_SIZE:
                    # Raya negra
                    pygame.draw.rect(screen, BLACK, 
                                  (c*CELL_SIZE, r*CELL_SIZE + y_offset, CELL_SIZE, stripe_height))
                    y_offset += stripe_height + stripe_spacing
                    
            elif val == 1:
                pygame.draw.rect(screen, BLACK, (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE))
            else:
                pygame.draw.rect(screen, WHITE, (c*CELL_SIZE, r*CELL_SIZE, CELL_SIZE, CELL_SIZE))

    # Dibujar agente (círculo + flecha orientación)
    cx = agent.y * CELL_SIZE + CELL_SIZE // 2
    cy = agent.x * CELL_SIZE + CELL_SIZE // 2
    pygame.draw.circle(screen, RED, (cx, cy), CELL_SIZE // 3)

    # Flecha que indica orientación
    arrow_len = CELL_SIZE // 2
    if agent.orient == 'N':
        pygame.draw.polygon(screen, BLUE, [(cx, cy - arrow_len//2), (cx-8, cy-2), (cx+8, cy-2)])
    elif agent.orient == 'E':
        pygame.draw.polygon(screen, BLUE, [(cx + arrow_len//2, cy), (cx+2, cy-8), (cx+2, cy+8)])
    elif agent.orient == 'S':
        pygame.draw.polygon(screen, BLUE, [(cx, cy + arrow_len//2), (cx-8, cy+2), (cx+8, cy+2)])
    elif agent.orient == 'W':
        pygame.draw.polygon(screen, BLUE, [(cx - arrow_len//2, cy), (cx-2, cy-8), (cx-2, cy+8)])

    # Panel informativo más grande
    font = pygame.font.SysFont("consolas", 20)
    panel_x = COLS * CELL_SIZE + 20
    
    # Determinar texto del modo
    if mode == "automatic":
        mode_text = "AUTOMÁTICO"
    elif mode == "automatic_fast":
        mode_text = "AUTOMÁTICO RÁPIDO"
    else:
        mode_text = "PASO A PASO"
    
    lines = [
        f"MODO: {mode_text}",
        f"MAPA: {ROWS}x{COLS}",
        f"TABLA: {FILE_NAME}",
        f"ITERACIÓN: {iteracion}",
        f"Posición: ({agent.x}, {agent.y})",
        f"Orientación: {agent.orient} {get_direction_arrow(agent.orient)}",
        "",
        f"Percepción completa:",
        f"  Piso: {percep[0]}",
        f"  Izq: {percep[1]}  Cen: {percep[2]}  Der: {percep[3]}",
        f"  Contacto: {percep[4]}",
        "",
        f"Regla aplicada: #{regla_idx if regla_idx else 'Sin coincidencia'}",
        f"Acción(es): {', '.join(acciones)}",
        "",
        "Controles:",
        "• F1: Modo automático normal",
        "• F2: Modo paso a paso",
        "• F3: Modo automático rápido",
        "• ESC: Menú de salida",
        "",
        "Archivo CSV: Guardado automático"
    ]
    for i, text in enumerate(lines):
        t = font.render(text, True, TEXT)
        screen.blit(t, (panel_x, 30 + i*30))

# --- Mostrar menú de configuración del mapa ---
def show_map_config_menu(screen):
    font_title = pygame.font.SysFont("consolas", 28, bold=True)
    font_option = pygame.font.SysFont("consolas", 22)
    font_instruction = pygame.font.SysFont("consolas", 16)
    
    # Opciones del menú
    options = [
        ("Usar por defecto (11x11)", (11, 11)),
        ("Mediano (15x15)", (15, 15)),
        ("Grande (21x21)", (21, 21)),
        ("Personalizado (9x9 por defecto)", "custom")
    ]
    
    # Selección por defecto (primera opción)
    selected_index = 0
    
    # Loop principal
    running = True
    while running:
        # Limpiar pantalla
        screen.fill(WHITE)
        
        # Título
        title = font_title.render("CONFIGURACIÓN DEL MAPA", True, TEXT)
        title_rect = title.get_rect(center=(screen.get_width()//2, 80))
        screen.blit(title, title_rect)
        
        # Mostrar opciones
        y_offset = 150
        for i, (option_text, _) in enumerate(options):
            # Determinar color según si está seleccionada
            if i == selected_index:
                text_color = BLUE
                prefix = "► "
            else:
                text_color = TEXT
                prefix = "  "
            
            display_text = f"{prefix}{option_text}"
            option = font_option.render(display_text, True, text_color)
            option_rect = option.get_rect(center=(screen.get_width()//2, y_offset))
            screen.blit(option, option_rect)
            y_offset += 40
        
        # Instrucciones
        inst1 = font_instruction.render("Usa las flechas ↑↓ para navegar, ENTER para seleccionar", True, TEXT)
        inst2 = font_instruction.render("• Mapas más grandes = ventana más grande", True, TEXT)
        inst3 = font_instruction.render("• ESC: Salir", True, TEXT)
        
        inst1_rect = inst1.get_rect(center=(screen.get_width()//2, y_offset + 20))
        inst2_rect = inst2.get_rect(center=(screen.get_width()//2, y_offset + 50))
        inst3_rect = inst3.get_rect(center=(screen.get_width()//2, y_offset + 80))
        
        screen.blit(inst1, inst1_rect)
        screen.blit(inst2, inst2_rect)
        screen.blit(inst3, inst3_rect)
        
        pygame.display.flip()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    _, value = options[selected_index]
                    if value == "custom":
                        return show_custom_size_menu(screen)
                    else:
                        return value
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(options)

# --- Mostrar menú de tamaño personalizado ---
def show_custom_size_menu(screen):
    font_title = pygame.font.SysFont("consolas", 24, bold=True)
    font_text = pygame.font.SysFont("consolas", 20)
    font_input = pygame.font.SysFont("consolas", 18)
    
    screen.fill(WHITE)
    
    # Título
    title = font_title.render("TAMAÑO PERSONALIZADO", True, TEXT)
    title_rect = title.get_rect(center=(screen.get_width()//2, 100))
    screen.blit(title, title_rect)
    
    # Instrucciones
    inst1 = font_text.render("Ingresa las dimensiones del mapa:", True, TEXT)
    inst2 = font_text.render("Filas (mínimo 5, máximo 30):", True, TEXT)
    inst3 = font_text.render("Columnas (mínimo 5, máximo 30):", True, TEXT)
    inst4 = font_text.render("Presiona ENTER para confirmar", True, TEXT)
    inst5 = font_text.render("ESC para cancelar", True, TEXT)
    
    inst1_rect = inst1.get_rect(center=(screen.get_width()//2, 150))
    inst2_rect = inst2.get_rect(center=(screen.get_width()//2, 200))
    inst3_rect = inst3.get_rect(center=(screen.get_width()//2, 250))
    inst4_rect = inst4.get_rect(center=(screen.get_width()//2, 350))
    inst5_rect = inst5.get_rect(center=(screen.get_width()//2, 380))
    
    screen.blit(inst1, inst1_rect)
    screen.blit(inst2, inst2_rect)
    screen.blit(inst3, inst3_rect)
    screen.blit(inst4, inst4_rect)
    screen.blit(inst5, inst5_rect)
    
    # Campos de entrada con valores por defecto
    rows_input = "9"
    cols_input = "9"
    current_input = "rows"  # "rows" o "cols"
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    try:
                        rows = int(rows_input) if rows_input else 9
                        cols = int(cols_input) if cols_input else 9
                        if 5 <= rows <= 30 and 5 <= cols <= 30:
                            return (rows, cols)
                        else:
                            # Mostrar error
                            error_text = font_text.render("Error: Dimensiones deben estar entre 5 y 30", True, RED)
                            error_rect = error_text.get_rect(center=(screen.get_width()//2, 420))
                            screen.blit(error_text, error_rect)
                            pygame.display.flip()
                            pygame.time.wait(2000)
                            return show_custom_size_menu(screen)
                    except ValueError:
                        # Mostrar error
                        error_text = font_text.render("Error: Ingresa números válidos", True, RED)
                        error_rect = error_text.get_rect(center=(screen.get_width()//2, 420))
                        screen.blit(error_text, error_rect)
                        pygame.display.flip()
                        pygame.time.wait(2000)
                        return show_custom_size_menu(screen)
                elif event.key == pygame.K_TAB:
                    current_input = "cols" if current_input == "rows" else "rows"
                elif event.key == pygame.K_BACKSPACE:
                    if current_input == "rows":
                        rows_input = rows_input[:-1]
                    else:
                        cols_input = cols_input[:-1]
                elif event.unicode.isdigit():
                    if current_input == "rows" and len(rows_input) < 2:
                        rows_input += event.unicode
                    elif current_input == "cols" and len(cols_input) < 2:
                        cols_input += event.unicode
        
        # Redibujar pantalla
        screen.fill(WHITE)
        screen.blit(title, title_rect)
        screen.blit(inst1, inst1_rect)
        screen.blit(inst2, inst2_rect)
        screen.blit(inst3, inst3_rect)
        screen.blit(inst4, inst4_rect)
        screen.blit(inst5, inst5_rect)
        
        # Mostrar valores actuales
        rows_display = rows_input if rows_input else "9"
        cols_display = cols_input if cols_input else "9"
        
        rows_text = font_input.render(f"Filas: {rows_display}", True, TEXT)
        cols_text = font_input.render(f"Columnas: {cols_display}", True, TEXT)
        
        rows_text_rect = rows_text.get_rect(center=(screen.get_width()//2, 220))
        cols_text_rect = cols_text.get_rect(center=(screen.get_width()//2, 270))
        
        screen.blit(rows_text, rows_text_rect)
        screen.blit(cols_text, cols_text_rect)
        
        # Resaltar campo activo
        if current_input == "rows":
            pygame.draw.rect(screen, BLUE, (rows_text_rect.x-5, rows_text_rect.y-2, rows_text_rect.width+10, rows_text_rect.height+4), 2)
        else:
            pygame.draw.rect(screen, BLUE, (cols_text_rect.x-5, cols_text_rect.y-2, cols_text_rect.width+10, cols_text_rect.height+4), 2)
        
        pygame.display.flip()

# --- Función para guardar archivo CSV al final ---
def save_csv_data(csv_data, output_path):
    """Guarda todos los datos del CSV al final"""
    try:
        with open(output_path, "w", newline='', encoding='utf-8') as logfile:
            writer = csv.writer(logfile)
            writer.writerows(csv_data)
        print(f"Archivo guardado: {output_path}")
        print(f"Total de iteraciones registradas: {len(csv_data) - 1}")  # -1 por el encabezado
        return True
    except Exception as e:
        print(f"Error al guardar archivo: {e}")
        return False

# --- Mostrar menú de salida ---
def show_exit_menu(screen):
    font_title = pygame.font.SysFont("consolas", 28, bold=True)
    font_option = pygame.font.SysFont("consolas", 22)
    font_instruction = pygame.font.SysFont("consolas", 16)
    
    # Opciones del menú
    options = [
        ("Reiniciar recorrido del agente", "restart"),
        ("Volver al menú inicial", "main_menu"),
        ("Volver al menú de modo", "mode_menu"),
        ("Salir completamente", "exit")
    ]
    
    # Selección por defecto (primera opción)
    selected_index = 0
    
    # Loop principal
    running = True
    while running:
        # Limpiar pantalla
        screen.fill(WHITE)
        
        # Título
        title = font_title.render("¿QUÉ DESEAS HACER?", True, TEXT)
        title_rect = title.get_rect(center=(screen.get_width()//2, 100))
        screen.blit(title, title_rect)
        
        # Mostrar opciones
        y_offset = 180
        for i, (option_text, _) in enumerate(options):
            # Determinar color según si está seleccionada
            if i == selected_index:
                text_color = BLUE
                prefix = "► "
            else:
                text_color = TEXT
                prefix = "  "
            
            display_text = f"{prefix}{option_text}"
            option = font_option.render(display_text, True, text_color)
            option_rect = option.get_rect(center=(screen.get_width()//2, y_offset))
            screen.blit(option, option_rect)
            y_offset += 40
        
        # Instrucciones
        inst1 = font_instruction.render("Usa las flechas ↑↓ para navegar, ENTER para seleccionar", True, TEXT)
        inst2 = font_instruction.render("• ESC: Cancelar", True, TEXT)
        
        inst1_rect = inst1.get_rect(center=(screen.get_width()//2, y_offset + 20))
        inst2_rect = inst2.get_rect(center=(screen.get_width()//2, y_offset + 50))
        
        screen.blit(inst1, inst1_rect)
        screen.blit(inst2, inst2_rect)
        
        pygame.display.flip()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "cancel"
                elif event.key == pygame.K_RETURN:
                    _, value = options[selected_index]
                    return value
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(options)
                # Mantener compatibilidad con números
                elif event.key == pygame.K_1:
                    return "restart"
                elif event.key == pygame.K_2:
                    return "main_menu"
                elif event.key == pygame.K_3:
                    return "mode_menu"
                elif event.key == pygame.K_4:
                    return "exit"

# --- Mostrar menú de selección de modo ---
def show_mode_menu(screen):
    font_title = pygame.font.SysFont("consolas", 32, bold=True)
    font_option = pygame.font.SysFont("consolas", 24)
    font_instruction = pygame.font.SysFont("consolas", 18)
    
    # Opciones del menú
    options = [
        ("Modo AUTOMÁTICO (F1)", "automatic"),
        ("Modo PASO A PASO (F2)", "step_by_step"),
        ("Modo AUTOMÁTICO RÁPIDO (F3)", "automatic_fast")
    ]
    
    # Selección por defecto (primera opción)
    selected_index = 0
    
    # Loop principal
    running = True
    while running:
        # Limpiar pantalla
        screen.fill(WHITE)
        
        # Título
        title = font_title.render("AGENTE REFLEJO SIMPLE", True, TEXT)
        title_rect = title.get_rect(center=(screen.get_width()//2, 100))
        screen.blit(title, title_rect)
        
        # Mostrar opciones
        y_offset = 180
        for i, (option_text, _) in enumerate(options):
            # Determinar color según si está seleccionada
            if i == selected_index:
                text_color = BLUE
                prefix = "► "
            else:
                text_color = TEXT
                prefix = "  "
            
            display_text = f"{prefix}{option_text}"
            option = font_option.render(display_text, True, text_color)
            option_rect = option.get_rect(center=(screen.get_width()//2, y_offset))
            screen.blit(option, option_rect)
            y_offset += 40
        
        # Instrucciones
        inst1 = font_instruction.render("Usa las flechas ↑↓ para navegar, ENTER para seleccionar", True, TEXT)
        inst2 = font_instruction.render("Durante la ejecución:", True, TEXT)
        inst3 = font_instruction.render("• F1: Modo automático normal", True, TEXT)
        inst4 = font_instruction.render("• F2: Modo paso a paso", True, TEXT)
        inst5 = font_instruction.render("• F3: Modo automático rápido", True, TEXT)
        inst6 = font_instruction.render("• ESC: Salir", True, TEXT)
        
        inst1_rect = inst1.get_rect(center=(screen.get_width()//2, y_offset + 20))
        inst2_rect = inst2.get_rect(center=(screen.get_width()//2, y_offset + 50))
        inst3_rect = inst3.get_rect(center=(screen.get_width()//2, y_offset + 80))
        inst4_rect = inst4.get_rect(center=(screen.get_width()//2, y_offset + 110))
        inst5_rect = inst5.get_rect(center=(screen.get_width()//2, y_offset + 140))
        inst6_rect = inst6.get_rect(center=(screen.get_width()//2, y_offset + 170))
        
        screen.blit(inst1, inst1_rect)
        screen.blit(inst2, inst2_rect)
        screen.blit(inst3, inst3_rect)
        screen.blit(inst4, inst4_rect)
        screen.blit(inst5, inst5_rect)
        screen.blit(inst6, inst6_rect)
        
        pygame.display.flip()
        
        # Procesar eventos
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return None
                elif event.key == pygame.K_RETURN:
                    _, value = options[selected_index]
                    return value
                elif event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(options)
                # Mantener compatibilidad con teclas F1-F3 y números
                elif event.key == pygame.K_F1 or event.key == pygame.K_1:
                    return "automatic"
                elif event.key == pygame.K_F2 or event.key == pygame.K_2:
                    return "step_by_step"
                elif event.key == pygame.K_F3 or event.key == pygame.K_3:
                    return "automatic_fast"

# --- Programa principal ---
def main():
    pygame.init()
    
    # Mostrar menú de selección de tabla primero
    temp_screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Selección de tabla de reglas")
    selected_table = show_table_selection_menu(temp_screen)
    if selected_table is None:
        pygame.quit()
        return
    
    # Mostrar menú de configuración del mapa
    pygame.display.set_caption("Configuración del mapa")
    map_size = show_map_config_menu(temp_screen)
    if map_size is None:
        pygame.quit()
        return
    
    # Llamar a la función de simulación con la tabla seleccionada
    run_simulation(map_size, selected_table)

# --- Función de simulación ---
def run_simulation(map_size, selected_table):
    
    # Configurar dimensiones globales
    global ROWS, COLS, CELL_SIZE, FILE_NAME
    ROWS, COLS = map_size
    FILE_NAME = selected_table
    
    # Crear ventana principal con el tamaño correcto
    panel_width = 400
    screen_width = (COLS * CELL_SIZE) + panel_width
    screen_height = ROWS * CELL_SIZE
    
    # Ajustar tamaño de ventana si es muy grande
    max_width, max_height = 1920, 1080
    if screen_width > max_width:
        CELL_SIZE = (max_width - panel_width) // COLS
        screen_width = (COLS * CELL_SIZE) + panel_width
        screen_height = ROWS * CELL_SIZE
    
    if screen_height > max_height:
        CELL_SIZE = max_height // ROWS
        screen_width = (COLS * CELL_SIZE) + panel_width
        screen_height = ROWS * CELL_SIZE
    
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Agente reflejo simple")
    clock = pygame.time.Clock()
    
    # Mostrar menú de selección de modo
    mode = show_mode_menu(screen)
    if mode is None:
        pygame.quit()
        return
    
    # Configurar título según el modo
    if mode == "automatic":
        pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO (F1/F2/F3 para cambiar)")
    elif mode == "automatic_fast":
        pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO RÁPIDO (F1/F2/F3 para cambiar)")
    else:
        pygame.display.set_caption("Agente reflejo simple - Modo PASO A PASO (ENTER/F1/F2/F3)")

    grid = create_map(ROWS, COLS, density=DENSITY)
    tabla, rule_indices = load_table(FILE_NAME)
    agent = Agent(grid)
    iteracion = 0

    # Percepción inicial
    percep = sense(grid, agent)
    acciones, percep_actual, regla_idx = decide(percep, tabla, rule_indices)

    running = True
    step_ready = False  # bandera: solo avanza al presionar ENTER
    auto_step_timer = pygame.time.get_ticks()  # timer para modo automático - inicializar con tiempo actual
    # Configurar velocidad inicial según el modo seleccionado
    if mode == "automatic_fast":
        AUTO_STEP_INTERVAL = 50  # milisegundos entre pasos automáticos (súper rápido)
    else:
        AUTO_STEP_INTERVAL = 200  # milisegundos entre pasos automáticos (normal)

    # --- Crear carpeta y archivo CSV de salida ---
    os.makedirs("salida", exist_ok=True)
    timestamp = datetime.now().strftime("%d%m%Y-%H%M%S")
    output_path = os.path.join("salida", f"salida-{timestamp}.csv")

    # Preparar datos para guardar al final
    csv_data = []
    csv_data.append([
        "#",
        "Pos",
        "Orientación",
        "Piso",
        "Izquierda",
        "Centro",
        "Derecha",
        "Contacto",
        "Regla",
        "Acción",
        "Nueva Pos",
        "Nueva Orientación"
    ])

    while running:
        current_time = pygame.time.get_ticks()
        
        # Procesar eventos de forma no bloqueante
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                # Guardar archivo antes de cerrar
                save_csv_data(csv_data, output_path)
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN and mode == "step_by_step":  # ENTER solo en modo paso a paso
                    step_ready = True
                elif ev.key == pygame.K_F1:  # Cambiar a modo automático
                    mode = "automatic"
                    AUTO_STEP_INTERVAL = 200  # Velocidad normal
                    pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO (F1/F2/F3 para cambiar)")
                    auto_step_timer = current_time  # Reset timer
                elif ev.key == pygame.K_F2:  # Cambiar a modo paso a paso
                    mode = "step_by_step"
                    pygame.display.set_caption("Agente reflejo simple - Modo PASO A PASO (ENTER/F1/F2/F3)")
                    step_ready = False
                elif ev.key == pygame.K_F3:  # Modo automático súper rápido
                    mode = "automatic_fast"
                    AUTO_STEP_INTERVAL = 50  # Velocidad súper rápida
                    pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO RÁPIDO (F1/F2/F3 para cambiar)")
                    auto_step_timer = current_time  # Reset timer
                elif ev.key == pygame.K_ESCAPE:
                    # Mostrar menú de salida
                    exit_choice = show_exit_menu(screen)
                    if exit_choice == "restart":
                        # Guardar archivo actual antes de reiniciar
                        save_csv_data(csv_data, output_path)
                        
                        # Crear nuevo archivo para el nuevo recorrido
                        timestamp = datetime.now().strftime("%d%m%Y-%H%M%S")
                        output_path = os.path.join("salida", f"salida-{timestamp}.csv")
                        csv_data = []
                        csv_data.append([
                            "#", "Pos", "Orientación", "Piso", "Izquierda", "Centro", 
                            "Derecha", "Contacto", "Regla", "Acción", "Nueva Pos", "Nueva Orientación"
                        ])
                        
                        # Reiniciar agente en la misma posición
                        agent = Agent(grid)
                        iteracion = 0
                        percep = sense(grid, agent)
                        acciones, percep_actual, regla_idx = decide(percep, tabla, rule_indices)
                        step_ready = False
                        auto_step_timer = pygame.time.get_ticks()
                    elif exit_choice == "main_menu":
                            # Guardar archivo antes de salir
                            save_csv_data(csv_data, output_path)
                            pygame.quit()
                            restart_main()
                            return
                    elif exit_choice == "mode_menu":
                        # Guardar archivo antes de cambiar modo
                        save_csv_data(csv_data, output_path)
                        
                        # Crear nuevo archivo para el nuevo modo
                        timestamp = datetime.now().strftime("%d%m%Y-%H%M%S")
                        output_path = os.path.join("salida", f"salida-{timestamp}.csv")
                        csv_data = []
                        csv_data.append([
                            "#", "Pos", "Orientación", "Piso", "Izquierda", "Centro", 
                            "Derecha", "Contacto", "Regla", "Acción", "Nueva Pos", "Nueva Orientación"
                        ])
                        
                        # Volver al menú de modo
                        mode = show_mode_menu(screen)
                        if mode is None:
                            running = False
                        else:
                            # Configurar título según el modo
                            if mode == "automatic":
                                pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO (F1/F2/F3 para cambiar)")
                            elif mode == "automatic_fast":
                                pygame.display.set_caption("Agente reflejo simple - Modo AUTOMÁTICO RÁPIDO (F1/F2/F3 para cambiar)")
                            else:
                                pygame.display.set_caption("Agente reflejo simple - Modo PASO A PASO (ENTER/F1/F2/F3)")
                            
                            # Configurar velocidad inicial según el modo seleccionado
                            if mode == "automatic_fast":
                                AUTO_STEP_INTERVAL = 50
                            else:
                                AUTO_STEP_INTERVAL = 200
                            
                            # Reiniciar agente
                            agent = Agent(grid)
                            iteracion = 0
                            percep = sense(grid, agent)
                            acciones, percep_actual, regla_idx = decide(percep, tabla, rule_indices)
                            step_ready = False
                            auto_step_timer = pygame.time.get_ticks()
                    elif exit_choice == "exit":
                        # Guardar archivo antes de salir completamente
                        save_csv_data(csv_data, output_path)
                        running = False
                        # Si es "cancel", continúa la ejecución normal

        # --- Lógica de avance según el modo ---
        should_step = False
        
        if mode == "step_by_step":
            should_step = step_ready
        elif mode in ["automatic", "automatic_fast"]:
            # En modo automático, avanzar cada AUTO_STEP_INTERVAL milisegundos
            if current_time - auto_step_timer >= AUTO_STEP_INTERVAL:
                should_step = True
                auto_step_timer = current_time
            
        if should_step:
            # Copia por seguridad (por si acciones es una lista reutilizada)
            acciones_a_ejecutar = list(acciones)
            iteracion += 1

            # Guardar estado inicial (antes de ejecutar las acciones)
            pos_inicial = (agent.x, agent.y)
            orient_inicial = agent.orient
            orient_symbol_inicial = {'N': '^', 'E': '>', 'S': 'v', 'W': '<'}[orient_inicial]
            piso_inicial, izq_inicial, cen_inicial, der_inicial, contacto_inicial = percep_actual

            # Ejecuta TODAS las acciones de la regla actual, en orden
            for a in acciones_a_ejecutar:
                ejecutar(agent, grid, a)
                # Actualizar percepción después de cada acción para el display
                percep_nuevo = sense(grid, agent)
                draw(screen, grid, agent, percep_nuevo, [a], iteracion, regla_idx, mode)
                pygame.display.flip()

            # Guardar estado final (después de ejecutar todas las acciones)
            pos_final = (agent.x, agent.y)
            orient_final = agent.orient
            orient_symbol_final = {'N': '^', 'E': '>', 'S': 'v', 'W': '<'}[orient_final]

            # Concatenar todas las acciones con " y "
            acciones_concatenadas = " y ".join(acciones_a_ejecutar)

            # Agregar datos a la lista en memoria (se guardará al final)
            csv_data.append([
                iteracion,
                f"[{pos_inicial[0]},{pos_inicial[1]}]",
                orient_symbol_inicial,
                piso_inicial,
                izq_inicial,
                cen_inicial,
                der_inicial,
                contacto_inicial,
                f"#{regla_idx if regla_idx else '-'}",
                acciones_concatenadas,
                f"[{pos_final[0]},{pos_final[1]}]",
                orient_symbol_final
            ])

            # Al terminar TODAS las acciones de la regla, prepara la siguiente regla
            percep_actual = sense(grid, agent)
            # si tu decide devuelve también regla_idx, úsalo aquí:
            acciones, percep_actual, regla_idx = decide(percep_actual, tabla, rule_indices)
            #acciones, percep_actual = decide(percep_actual, tabla)

            # Reset step_ready solo en modo paso a paso
            if mode == "step_by_step":
                step_ready = False  # espera la siguiente pulsación de ENTER

        # --- Dibuja siempre el estado actual aunque no se mueva ---
        draw(screen, grid, agent, percep_actual, acciones, iteracion, regla_idx, mode)
        pygame.display.flip()
        clock.tick(FPS)

    # Guardar archivo antes de cerrar el programa
    save_csv_data(csv_data, output_path)
    pygame.quit()

# --- Función recursiva para reiniciar ---
def restart_main():
    pygame.quit()
    main()

if __name__ == "__main__":
    main()
