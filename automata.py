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
            Estado.EN_TIERRA.value: [Estado.DESPEGANDO.value, Estado.EMERGENCIA.value],
            Estado.DESPEGANDO.value: [Estado.EN_VUELO.value, Estado.EMERGENCIA.value],
            Estado.EN_VUELO.value: [Estado.ATERRIZANDO.value, Estado.EMERGENCIA.value],
            Estado.ATERRIZANDO.value: [Estado.EN_TIERRA.value, Estado.EMERGENCIA.value],
            Estado.EMERGENCIA.value: [Estado.EN_TIERRA.value]
        }
        self.historial = [(None, Estado.EN_TIERRA)]

    def transicionar(self, estado_siguiente):
        if estado_siguiente.value in self.transiciones.get(self.estado_actual.value, []):
            self.historial.append((self.estado_actual, estado_siguiente))
            self.estado_actual = estado_siguiente
            return True, f"Transición exitosa a {self.estado_actual.value}"
        else:
            mensaje_error = f"Transición inválida desde el estado {self.estado_actual.value} no se puede ir al estado  {estado_siguiente.value}."
            print(f"Mensaje de error: {mensaje_error}")
            return False, mensaje_error

# Configuración de la página de Streamlit
st.set_page_config(page_title="Simulador de Aeronave", layout="wide")
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
if 'estado_objetivo' not in st.session_state:
    st.session_state.estado_objetivo = Estado.EN_TIERRA.value

# Restaurar el estado del autómata
automata = st.session_state.automata
automata.estado_actual = Estado(st.session_state.estado_actual)

# Diseño de la interfaz con 3 columnas
col1, col2, col3 = st.columns([1, 2, 1])

# Columna 1: Controles de la simulación
with col1:
    st.subheader("Control de Estados")
    st.write(f"Estado actual: {automata.estado_actual.value}")
    estado_siguiente = st.selectbox("Seleccionar siguiente estado:", [s.value for s in Estado], key="seleccion_estado")
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
        st.session_state.estado_objetivo = Estado.EN_TIERRA.value
        st.rerun()

    if boton_transicion:
        exito, mensaje = automata.transicionar(Estado[estado_siguiente])
        st.session_state.exito = exito
        st.session_state.mensaje = mensaje
        if exito:
            st.session_state.estado_actual = automata.estado_actual.value
            st.session_state.estado_ultimo = automata.estado_actual.value
            st.session_state.estado_objetivo = estado_siguiente
            st.success(mensaje)
        else:
            st.session_state.estado_objetivo = estado_siguiente
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
        # Dibujar nodos con doble círculo para EN_TIERRA (estado terminal)
        if estado == "EN_TIERRA":
            codigo_estados += (
                "ctx.beginPath();\n"
                f"ctx.arc({pos[0]}, {pos[1]}, 20, 0, 2 * Math.PI);\n"
                f"ctx.fillStyle = '{estado}' === '{automata.estado_actual.value}' ? 'green' : 'lightgray';\n"
                "ctx.fill();\n"
                "ctx.stroke();\n"
                # Segundo círculo más pequeño para indicar estado terminal
                "ctx.beginPath();\n"
                f"ctx.arc({pos[0]}, {pos[1]}, 23, 0, 2 * Math.PI);\n"
                "ctx.strokeStyle = 'black';\n"
                "ctx.lineWidth = 2;\n"
                "ctx.stroke();\n"
                "ctx.lineWidth = 1;\n"
                "ctx.fillStyle = 'black';\n"
                "ctx.font = '12px Arial';\n"
                f"ctx.fillText('{estado}', {pos[0] - 30}, {pos[1] - 25});\n"
                f"ctx.fillText('{abbreviations[estado]}', {pos[0] - 5}, {pos[1] + 5});\n"
            )
        else:
            codigo_estados += (
                "ctx.beginPath();\n"
                f"ctx.arc({pos[0]}, {pos[1]}, 20, 0, 2 * Math.PI);\n"
                f"ctx.fillStyle = '{estado}' === '{automata.estado_actual.value}' ? 'green' : 'lightgray';\n"
                "ctx.fill();\n"
                "ctx.stroke();\n"
                "ctx.fillStyle = 'black';\n"
                "ctx.font = '12px Arial';\n"
                f"ctx.fillText('{estado}', {pos[0] - 30}, {pos[1] - 25});\n"
                f"ctx.fillText('{abbreviations[estado]}', {pos[0] - 5}, {pos[1] + 5});\n"
            )

    # Agregar flecha inicial apuntando a EN_TIERRA
    flecha_inicial = (
        "ctx.beginPath();\n"
        "ctx.moveTo(70, 400);\n"  # Punto de inicio de la flecha (a la izquierda de EN_TIERRA)
        "ctx.lineTo(80, 400);\n"  # Punto final cerca del nodo EN_TIERRA
        "ctx.strokeStyle = 'black';\n"
        "ctx.lineWidth = 2;\n"
        "ctx.stroke();\n"
        # Dibujar punta de flecha
        "ctx.beginPath();\n"
        "ctx.moveTo(80, 400);\n"
        "ctx.lineTo(75, 395);\n"
        "ctx.lineTo(75, 405);\n"
        "ctx.fillStyle = 'black';\n"
        "ctx.fill();\n"
        "ctx.lineWidth = 1;\n"
    )

    js_code = f"""
    <canvas id="simulacionCanvas" width="600" height="450" style="border:1px solid black;"></canvas>
    <script>
        const canvas = document.getElementById('simulacionCanvas');
        const ctx = canvas.getContext('2d');
        let avionX = {posiciones[automata.estado_actual.value][0]};
        let avionY = {posiciones[automata.estado_actual.value][1]};
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
            ctx.fillRect(0, 350, canvas.width, 100);
            
            {flecha_inicial}
            {codigo_estados}

            ctx.font = '30px Arial';
            ctx.fillText('✈️', avionX - 15, avionY + 10);

            if (error) {{
                ctx.strokeStyle = 'red';
                ctx.lineWidth = 5;
                ctx.beginPath();
                ctx.moveTo(errorX - 20, errorY - 20);
                ctx.lineTo(errorX + 20, errorY + 20);
                ctx.moveTo(errorX + 20, errorY - 20);
                ctx.lineTo(errorX - 20, errorY + 20);
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
                errorX = {posiciones.get(st.session_state.estado_objetivo, [0, 0])[0]};
                errorY = {posiciones.get(st.session_state.estado_objetivo, [0, 0])[1]};
                setTimeout(() => {{ error = false; dibujar(); }}, 1000);
            }} else {{
                error = false;
                objetivoX = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[0]};
                objetivoY = {posiciones.get(st.session_state.estado_ultimo, [0, 0])[1]};
            }}
            requestAnimationFrame(dibujar);
        }}

        dibujar();
        {'actualizarPosicion("' + st.session_state.estado_objetivo + '", ' + ('true' if not st.session_state.exito else 'false') + ');' if boton_transicion else ''}
    </script>
    """
    st.components.v1.html(js_code, height=460)

# Columna 3: Visualización del DFA
with col3:
    st.subheader("Autómata Finito Determinista")
    red = Network(directed=True, height="450px", width="100%", bgcolor="#f0f8ff", font_color="red")
    red.set_options("""
    {
        "nodes": {
            "shape": "dot",
            "size": 40,
            "font": {
                "size": 12,
                "color": "black",
                "multi": "html"
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
                "type": "continuous"
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

    # Posiciones fijas para los nodos del DFA, con EMERGENCIA en el centro
    dfa_posiciones = {
        "EN_TIERRA": {"x": -200, "y": 150},
        "DESPEGANDO": {"x": -280, "y": 0},
        "EN_VUELO": {"x": -60, "y": -220},
        "ATERRIZANDO": {"x": 100, "y": 0},
        "EMERGENCIA": {"x": -30, "y": 0},
        "INICIAL": {"x": -300, "y": 150}  # Nodo auxiliar para la flecha inicial
    }

    # Agregar nodos
    for estado in Estado:
        color = "green" if estado == automata.estado_actual else "#97c2fc"
        label = f"<b>{abbreviations[estado.value]}</b>"
        # Usar borde más grueso para EN_TIERRA para simular doble círculo (estado terminal)
        border_width = 6 if estado.value == "EN_TIERRA" else 1
        red.add_node(
            estado.value,
            label=label,
            title=estado.value.replace('_', ' '),
            color={"background": color, "border": "black"},
            size=40,
            shape="dot",
            font={"size": 12, "color": "black", "multi": "html"},
            x=dfa_posiciones[estado.value]["x"],
            y=dfa_posiciones[estado.value]["y"],
            fixed=True,
            borderWidth=border_width
        )

    # Agregar nodo auxiliar para la flecha inicial
    red.add_node(
        "INICIAL",
        label="",
        size=10,
        shape="dot",
        color={"background": "#f0f8ff", "border": "#f0f8ff"},  # Invisible (mismo color que el fondo)
        x=dfa_posiciones["INICIAL"]["x"],
        y=dfa_posiciones["INICIAL"]["y"],
        fixed=True
    )
    # Flecha desde el nodo auxiliar a EN_TIERRA
    red.add_edge("INICIAL", "EN_TIERRA", color="#2b7ce9", width=2)

    # Agregar aristas de las transiciones
    for estado_origen, estados_destino in automata.transiciones.items():
        for estado_destino in estados_destino:
            red.add_edge(estado_origen, estado_destino, color="#2b7ce9", width=2)

    red.save_graph("dfa.html")
    with open("dfa.html", "r", encoding="utf-8") as f:
        st.components.v1.html(f.read(), height=460)
    os.remove("dfa.html")

# Sección de historial de transiciones
st.subheader("Historial de Transiciones")
if len(automata.historial) > 1:
    for i, (estado_origen, estado_destino) in enumerate(automata.historial[1:], 1):
        st.write(f"{i}. {estado_origen.value if estado_origen else 'Inicio'} → {estado_destino.value}")
else:
    st.write("No hay transiciones aún.")