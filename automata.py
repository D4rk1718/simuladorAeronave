import streamlit as st
from enum import Enum
from pyvis.network import Network
import os
import json

# Definición de los estados de la aeronave usando un Enum
class Estado(Enum):
    EN_TIERRA = "EN_TIERRA"
    DESPEGANDO = "DESPEGANDO"
    EN_VUELO = "EN_VUELO"
    ATERRIZANDO = "ATERRIZANDO"
    EMERGENCIA = "EMERGENCIA"

# Abreviaturas para los estados
abbreviations = {
    "EN_TIERRA": "T",   
    "DESPEGANDO": "D",
    "EN_VUELO": "V",
    "ATERRIZANDO": "A",
    "EMERGENCIA": "E"
}

# Clase que representa el autómata finito determinista (DFA) de la aeronave
class AutomataAeronave:
    def __init__(self):
        self.estado_actual = Estado.EN_TIERRA
        self.transiciones = {
            Estado.EN_TIERRA.value: {
                "iniciar_despegue": Estado.DESPEGANDO.value,
                "emergencia": Estado.EMERGENCIA.value
            },
            Estado.DESPEGANDO.value: {
                "alcanzar_altitud_crucero": Estado.EN_VUELO.value,
                "emergencia": Estado.EMERGENCIA.value
            },
            Estado.EN_VUELO.value: {
                "iniciar_aterrizaje": Estado.ATERRIZANDO.value,
                "emergencia": Estado.EMERGENCIA.value
            },
            Estado.ATERRIZANDO.value: {
                "tocar_tierra": Estado.EN_TIERRA.value,
                "emergencia": Estado.EMERGENCIA.value
            },
            Estado.EMERGENCIA.value: {
                "tocar_tierra": Estado.EN_TIERRA.value,
                "emergencia": Estado.EMERGENCIA.value
            }
        }
        self.historial = [(None, Estado.EN_TIERRA)]

    def transicionar(self, simbolo):
        estado_siguiente = None
        error_mensaje = None

        # Verificar si el símbolo es válido para el estado actu
        if simbolo in self.transiciones.get(self.estado_actual.value, {}):
            estado_siguiente = Estado(self.transiciones[self.estado_actual.value][simbolo])
        else:
            # Mensajes de error específicos y más descriptivos
            if self.estado_actual.value == "EN_TIERRA":
                error_mensaje = f"Error Operacional: No puedes {simbolo.replace('_', ' ')} desde EN_TIERRA. La aeronave debe iniciar el despegue primero. Usa 'iniciar_despegue' o 'emergencia'."
            elif self.estado_actual.value == "DESPEGANDO":
                error_mensaje = f"Error Operacional: No puedes {simbolo.replace('_', ' ')} desde DESPEGANDO. La aeronave está en proceso de despegue. Usa 'alcanzar_altitud_crucero' o 'emergencia'."
            elif self.estado_actual.value == "EN_VUELO":
                error_mensaje = f"Error Operacional: No puedes {simbolo.replace('_', ' ')} desde EN_VUELO. La aeronave está en altitud de crucero. Usa 'iniciar_aterrizaje' o 'emergencia'."
            elif self.estado_actual.value == "ATERRIZANDO":
                error_mensaje = f"Error Operacional: No puedes {simbolo.replace('_', ' ')} desde ATERRIZANDO. La aeronave está descendiendo. Usa 'tocar_tierra' o 'emergencia'."
            elif self.estado_actual.value == "EMERGENCIA":
                error_mensaje = f"Error Operacional: No puedes {simbolo.replace('_', ' ')} desde EMERGENCIA. La aeronave está en estado de emergencia. Usa 'tocar_tierra' o 'emergencia' para continuar."
            else:
                error_mensaje = f"Error Operacional: Símbolo '{simbolo}' no válido desde el estado {self.estado_actual.value}."

        if estado_siguiente:
            self.historial.append((self.estado_actual, estado_siguiente))
            self.estado_actual = estado_siguiente
            return True, f"Transición exitosa a {self.estado_actual.value} con símbolo {simbolo.replace('_', ' ')}"
        else:
            print(f"Mensaje de error: {error_mensaje}")
            return False, error_mensaje
# Configuración de la página de Streamlit
st.set_page_config(page_title="Simulador de Aeronave", layout="wide")

# CSS personalizado para responsividad
st.markdown("""
<style>
/* Ajustar contenedores para pantallas pequeñas */
.stApp {
    max-width: 100%;
    padding: 1rem;
}

/* Hacer las columnas apilables en pantallas pequeñas */
@media (max-width: 768px) {
    .st-col {
        flex: 100% !important;
        max-width: 100% !important;
        margin-bottom: 1rem;
    }
}

/* Ajustar el canvas para que sea responsive */
#simulacionCanvas {
    width: 100% !important;
    height: auto !important;
    max-height: 400px;
}

/* Ajustar el contenedor del DFA */
div[data-testid="stVerticalBlock"] > div {
    width: 100% !important;
}

/* Ajustar el texto y botones para móviles */
.stButton > button {
    width: 100%;
    font-size: 16px;
}
.stSelectbox {
    width: 100%;
}
.stMarkdown {
    font-size: 14px;
}

/* Ajustar el historial para evitar desbordamiento */
.historial {
    max-height: 200px;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

st.title("Simulador de Aeronave")

# Inicialización del estado persistente
if 'automata' not in st.session_state:
    st.session_state.automata = AutomataAeronave()
if 'estado_actual' not in st.session_state:
    st.session_state.estado_actual = Estado.EN_TIERRA.value
if 'reiniciar' not in st.session_state:
    st.session_state.reiniciar = False
if 'exito' not in st.session_state:
    st.session_state.exito = True
if 'mensaje' not in st.session_state:
    st.session_state.mensaje = ""
if 'estado_ultimo' not in st.session_state:
    st.session_state.estado_ultimo = Estado.EN_TIERRA.value
if 'simbolo_objetivo' not in st.session_state:
    st.session_state.simbolo_objetivo = "iniciar_despegue"

# Restaurar el estado del autómata
automata = st.session_state.automata
automata.estado_actual = Estado(st.session_state.estado_actual)

# Diseño de la interfaz con columnas responsivas
col1, col2, col3 = st.columns([1, 2, 1], gap="medium")

# Columna 1: Controles de la simulación
with col1:
    st.subheader("Control de Estados")
    st.write(f"Estado actual: {automata.estado_actual.value}")
    simbolo = st.selectbox(
        "Seleccionar símbolo del alfabeto:",
        ["iniciar_despegue", "alcanzar_altitud_crucero", "iniciar_aterrizaje", "tocar_tierra", "emergencia"],
        key="seleccion_simbolo"
    )
    boton_transicion = st.button("Realizar Transición")
    boton_reiniciar = st.button("Reiniciar Simulación")

    # Leyenda de abreviaturas
    st.subheader("Leyenda")
    for estado, abbr in abbreviations.items():
        st.write(f"{abbr} = {estado.replace('_', ' ').title()}")

    if boton_reiniciar:
        st.session_state.automata = AutomataAeronave()
        st.session_state.estado_actual = Estado.EN_TIERRA.value
        st.session_state.reiniciar = True
        st.session_state.exito = True
        st.session_state.mensaje = ""
        st.session_state.estado_ultimo = Estado.EN_TIERRA.value
        st.session_state.simbolo_objetivo = "iniciar_despegue"
        st.rerun()

    if boton_transicion:
        exito, mensaje = automata.transicionar(simbolo)
        st.session_state.exito = exito
        st.session_state.mensaje = mensaje
        if exito:
            st.session_state.estado_actual = automata.estado_actual.value
            st.session_state.estado_ultimo = automata.estado_actual.value
            st.session_state.simbolo_objetivo = simbolo
            st.success(mensaje)
        else:
            st.session_state.simbolo_objetivo = simbolo
            st.error(mensaje)

# Columna 2: Simulación visual
with col2:
    st.subheader("Simulación")
    posiciones = {
        "EN_TIERRA": [100, 400],
        "DESPEGANDO": [200, 250],
        "EN_VUELO": [300, 100],
        "ATERRIZANDO": [400, 250],
        "EMERGENCIA": [300, 300]
    }

    codigo_estados = ""
    for estado, pos in posiciones.items():
        # Escalar posiciones según el tamaño del canvas
        scale_x = "canvas.width / 600"
        scale_y = "canvas.height / 450"
        pos_x = f"{pos[0]} * {scale_x}"
        pos_y = f"{pos[1]} * {scale_y}"
        if estado == "EN_TIERRA":
            codigo_estados += (
                "ctx.beginPath();\n"
                f"ctx.arc({pos_x}, {pos_y}, 20 * scale, 0, 2 * Math.PI);\n"
                f"ctx.fillStyle = '{estado}' === '{st.session_state.estado_actual}' ? 'green' : 'lightgray';\n"
                "ctx.fill();\n"
                "ctx.stroke();\n"
                "ctx.beginPath();\n"
                f"ctx.arc({pos_x}, {pos_y}, 23 * scale, 0, 2 * Math.PI);\n"
                "ctx.strokeStyle = 'black';\n"
                "ctx.lineWidth = 2 * scale;\n"
                "ctx.stroke();\n"
                "ctx.lineWidth = 1 * scale;\n"
                "ctx.fillStyle = 'black';\n"
                f"ctx.font = `${{12 * scale}}px Arial`;\n"
                f"ctx.fillText('{estado}', {pos_x} - (30 * scale), {pos_y} - (25 * scale));\n"
                f"ctx.fillText('{abbreviations[estado]}', {pos_x} - (5 * scale), {pos_y} + (5 * scale));\n"
            )
        else:
            codigo_estados += (
                "ctx.beginPath();\n"
                f"ctx.arc({pos_x}, {pos_y}, 20 * scale, 0, 2 * Math.PI);\n"
                f"ctx.fillStyle = '{estado}' === '{st.session_state.estado_actual}' ? 'green' : 'lightgray';\n"
                "ctx.fill();\n"
                "ctx.stroke();\n"
                "ctx.fillStyle = 'black';\n"
                f"ctx.font = `${{12 * scale}}px Arial`;\n"
                f"ctx.fillText('{estado}', {pos_x} - (30 * scale), {pos_y} - (25 * scale));\n"
                f"ctx.fillText('{abbreviations[estado]}', {pos_x} - (5 * scale), {pos_y} + (5 * scale));\n"
            )

    # Ajustar flecha inicial
    flecha_inicial = (
        "ctx.beginPath();\n"
        f"ctx.moveTo(70 * {scale_x}, 400 * {scale_y});\n"
        f"ctx.lineTo(80 * {scale_x}, 400 * {scale_y});\n"
        "ctx.strokeStyle = 'black';\n"
        "ctx.lineWidth = 2 * scale;\n"
        "ctx.stroke();\n"
        "ctx.beginPath();\n"
        f"ctx.moveTo(80 * {scale_x}, 400 * {scale_y});\n"
        f"ctx.lineTo(75 * {scale_x}, 395 * {scale_y});\n"
        f"ctx.lineTo(75 * {scale_x}, 405 * {scale_y});\n"
        "ctx.fillStyle = 'black';\n"
        "ctx.fill();\n"
        "ctx.lineWidth = 1 * scale;\n"
    )

    js_code = f"""
    <canvas id="simulacionCanvas" style="width: 100%; max-height: 400px;"></canvas>
    <script>
        const canvas = document.getElementById('simulacionCanvas');
        const ctx = canvas.getContext('2d');
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetWidth * (450 / 600);
        const scale = canvas.width / 600;
        let avionX = {posiciones[st.session_state.estado_actual][0]} * scale;
        let avionY = {posiciones[st.session_state.estado_actual][1]} * scale;
        let objetivoX = avionX;
        let objetivoY = avionY;
        let error = false;
        let errorX = 0;
        let errorY = 0;

        function dibujar() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'lightblue';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = 'gray';
            ctx.fillRect(0, 350 * scale, canvas.width, 100 * scale);
            
            {flecha_inicial}
            {codigo_estados}

            ctx.font = `${{30 * scale}}px Arial`;
            ctx.fillText('✈️', avionX - (15 * scale), avionY + (10 * scale));

            if (error) {{
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 5 * scale;
                ctx.beginPath();
                ctx.moveTo(errorX - (20 * scale), errorY - (20 * scale));
                ctx.lineTo(errorX + (20 * scale), errorY + (20 * scale));
                ctx.moveTo(errorX + (20 * scale), errorY - (20 * scale));
                ctx.lineTo(errorX - (20 * scale), errorY + (20 * scale));
                ctx.stroke();
            }}

            if (Math.abs(avionX - objetivoX) > 1 || Math.abs(avionY - objetivoY) > 1) {{
                avionX += (objetivoX - avionX) * 0.05;
                avionY += (objetivoY - avionY) * 0.05;
                requestAnimationFrame(dibujar);
            }}
        }}

        function actualizarPosicion(estadoObjetivo, hayError) {{
            if (hayError) {{
                error = true;
                errorX = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[0]} * scale;
                errorY = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[1]} * scale;
                setTimeout(() => {{ error = false; dibujar(); }}, 1000);
            }} else {{
                error = false;
                objetivoX = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[0]} * scale;
                objetivoY = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[1]} * scale;
            }}
            requestAnimationFrame(dibujar);
        }}

        // Ajustar canvas al redimensionar
        window.addEventListener('resize', () => {{
            canvas.width = canvas.offsetWidth;
            canvas.height = canvas.offsetWidth * (450 / 600);
            scale = canvas.width / 600;
            avionX = {posiciones[st.session_state.estado_actual][0]} * scale;
            avionY = {posiciones[st.session_state.estado_actual][1]} * scale;
            objetivoX = avionX;
            objetivoY = avionY;
            dibujar();
        }});

        dibujar();
        {'actualizarPosicion("' + st.session_state.estado_ultimo + '", ' + ('true' if not st.session_state.exito else 'false') + ');' if boton_transicion else ''}
    </script>
    """
    st.components.v1.html(js_code, height=400)

# Columna 3: Visualización del DFA
with col3:
    st.subheader("Autómata Finito Determinista")
    red = Network(directed=True, height="400px", width="100%", bgcolor="#f0f8ff", font_color="black")
    red.set_options("""
    {
        "nodes": {
            "shape": "dot",
            "size": 30,
            "font": {
                "size": 12,
                "color": "black",
                "multi": "html",
                "align": "center"
            }
        },
        "edges": {
            "color": {
                "inherit": false,
                "color": "#2b7ce9"
            },
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "smooth": {
                "type": "curvedCW",
                "roundness": 0.2
            },
            "font": {
                "size": 10,
                "color": "black",
                "align": "middle"
            }
        },
        "physics": {
            "enabled": false
        },
        "layout": {
            "improvedLayout": true
        }
    }
    """)

    # Positions for nodes
    dfa_posiciones = {
        "EN_TIERRA": {"x": -150, "y": 100},
        "DESPEGANDO": {"x": -200, "y": 0},
        "EN_VUELO": {"x": -50, "y": -150},
        "ATERRIZANDO": {"x": 80, "y": 0},
        "EMERGENCIA": {"x": -20, "y": 0},
        "INICIAL": {"x": -250, "y": 100}
    }

    # Add nodes
    for estado in Estado:
        color = "green" if estado.value == st.session_state.estado_actual else "#97c2fc"
        label = f"<b>{abbreviations[estado.value]}</b>"
        border_width = 4 if estado.value == "EN_TIERRA" else 1
        red.add_node(
            estado.value,
            label=label,
            title=estado.value.replace('_', ' '),
            color={"background": color, "border": "black"},
            size=30,
            shape="dot",
            font={"size": 12, "color": "black", "multi": "html", "align": "center"},
            x=dfa_posiciones[estado.value]["x"],
            y=dfa_posiciones[estado.value]["y"],
            fixed=True,
            borderWidth=border_width
        )

    # Add auxiliary initial node
    red.add_node(
        "INICIAL",
        label="",
        size=10,
        shape="dot",
        color={"background": "#f0f8ff", "border": "#f0f8ff"},
        x=dfa_posiciones["INICIAL"]["x"],
        y=dfa_posiciones["INICIAL"]["y"],
        fixed=True
    )
    red.add_edge("INICIAL", "EN_TIERRA", color="#2b7ce9", width=2, label="")

    # Add edges based on transitions
    for estado_origen, transiciones in automata.transiciones.items():
        for simbolo, estado_destino in transiciones.items():
            # Abreviar etiquetas para mejor visualización
            simbolo_abbr = {
                "iniciar_despegue": "ID",
                "alcanzar_altitud_crucero": "AAC",
                "iniciar_aterrizaje": "IA",
                "tocar_tierra": "TT",
                "emergencia": "E"
            }.get(simbolo, simbolo)
            red.add_edge(
                estado_origen,
                estado_destino,
                color="#2b7ce9",
                width=2,
                label=simbolo_abbr,
                font={"size": 10, "color": "black", "align": "middle"}
            )

    red.save_graph("dfa.html")
    with open("dfa.html", "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=400)
    os.remove("dfa.html")

# Transition history section
st.subheader("Historial de Transiciones")
with st.container():
    if len(automata.historial) > 1:
        for i, (estado_origen, estado_destino) in enumerate(automata.historial[1:], 1):
            st.write(f"{i}. {estado_origen.value if estado_origen else 'Inicio'} → {estado_destino.value}")
    else:
        st.write("No hay transiciones aún.")