import gevent
from gevent import monkey
monkey.patch_all()

import base64
from threading import Thread, Event
import pyautogui
from io import BytesIO
import gevent.monkey
from flask import Flask, request, jsonify, render_template, make_response, redirect, render_template_string, url_for, flash
import secrets
import os
import time
from flask_socketio import SocketIO
import socket
import json
import ssl
import bcrypt
import subprocess
import re



gevent.monkey.patch_all()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')
thread = Thread()
thread_stop_event = Event()

LONGITUD=150
app.secret_key = secrets.token_urlsafe(LONGITUD)

SOCKETIDLIST=[]
ACCESSTOKENLIST=[]
FRAMEQUALITY=60
FRAMEUPDATE=1
LASTTIMETOKENGENERATED=0
TOKENRESETTIME=86400

DATA_FOLDER = 'savedata'
os.makedirs(DATA_FOLDER, exist_ok=True)
FRAME_QUALITY_FILE = os.path.join(DATA_FOLDER, 'frameQuality.json')
FRAME_UPDATE_FILE = os.path.join(DATA_FOLDER, 'frameUpdate.json')
#END_FILE = os.path.join(DATA_FOLDER, 'end.pkl')



def get_hashed_password(username):
    try:
        with open(os.path.join(DATA_FOLDER, username), 'rb') as file:
            hashed_password = file.read()
        return hashed_password
    except FileNotFoundError:
        return None


def save_user(username, password):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    with open(os.path.join(DATA_FOLDER, username), 'wb') as file:
        file.write(hashed)


@app.route('/credentials', methods=['GET', 'POST'])
def cambiar_credenciales():
    if request.method == 'POST':
        usuario = request.form['username']
        contrasena = request.form['password']
        nuevo_usuario = request.form['new_username']
        nueva_contrasena = request.form['new_password']
        confirmacion = request.form['confirm_password']
        confirmacion_usuario = request.form['confirm_username']

        # Verifica que las nuevas credenciales coincidan
        if nueva_contrasena != confirmacion or nuevo_usuario != confirmacion_usuario:
            flash("La nueva contraseña o usuario no coincide con la confirmación.")
            return redirect(url_for('cambiar_credenciales'))

        # Obtiene la contraseña hasheada actual
        hashed_password = get_hashed_password(usuario)

        # Verifica las credenciales actuales
        if hashed_password and bcrypt.checkpw(contrasena.encode('utf-8'), hashed_password):
            # Actualiza las credenciales
            save_user(nuevo_usuario, nueva_contrasena)
            # Elimina el usuario antiguo si el nombre ha cambiado
            if nuevo_usuario != usuario:
                os.remove(os.path.join(DATA_FOLDER, usuario))
            flash("Credenciales actualizadas con éxito.")
            SOCKETIDLIST.clear()
            ACCESSTOKENLIST.clear()
            return redirect(url_for('cambiar_credenciales'))
        else:
            flash("Credenciales actuales incorrectas.")

    return render_template_string('''
        <!doctype html>
        <title>Cambio de credenciales</title>
        <link rel="icon" type="image/png" href="/static/images/favicon.png"> <!-- Favicon añadido aquí -->
        <h1>Cambio de credenciales</h1>
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            <ul>
            {% for message in messages %}
              <li>{{ message }}</li>
            {% endfor %}
            </ul>
          {% endif %}
        {% endwith %}
        <form method="post">
            Usuario actual: <input type="text" name="username" required><br>
            Contraseña actual: <input type="password" name="password" required><br>
            Nuevo usuario: <input type="text" name="new_username" required><br>
            Confirmar nuevo usuario: <input type="text" name="confirm_username" required><br>
            Nueva contraseña: <input type="password" name="new_password" required><br>
            Confirmar nueva contraseña: <input type="password" name="confirm_password" required><br>
            <input type="submit" value="Send">
        </form>
    ''')


def capture_and_send_screen():
    global FRAMEQUALITY,FRAMEUPDATE, LASTTIMETOKENGENERATED
    while not thread_stop_event.is_set():
        #print(SOCKETIDLIST)
        if time.time()-LASTTIMETOKENGENERATED>TOKENRESETTIME and LASTTIMETOKENGENERATED!=0:
            LASTTIMETOKENGENERATED=0
            #print("prueba")
            SOCKETIDLIST.clear()
            ACCESSTOKENLIST.clear()
        img = pyautogui.screenshot()

        # Codifica la imagen capturada en base64 y la envía
        output_buffer = BytesIO()
        img.save(output_buffer, format="JPEG", quality=FRAMEQUALITY)
        base64_img = base64.b64encode(output_buffer.getvalue()).decode('utf-8')  # Codifica a base64

        for socket_id in SOCKETIDLIST:
            socketio.emit('screen_capture', {'image': base64_img}, room=socket_id)

        time.sleep(FRAMEUPDATE)


@app.route('/show')
def index_show():
    global ACCESSTOKENLIST, FRAMEQUALITY, FRAMEUPDATE
    with open('savedata/frameQuality.json', 'r') as archivo:
        FRAMEQUALITY = json.load(archivo)  # Carga los datos del archivo
    with open('savedata/frameUpdate.json', 'r') as archivo:
        FRAMEUPDATE = json.load(archivo)  # Carga los datos del archivo

    CloudPCAccessSessionToken = request.cookies.get('CloudPCAccessSessionToken')

    if CloudPCAccessSessionToken in ACCESSTOKENLIST:
        return render_template('index.html')
    else:
        return "Access Denied or Token Expired", 403


@socketio.on('connect')
def on_connect():
    global thread, ACCESSTOKENLIST, SOCKETIDLIST

    print('Client connected')
    CloudPCAccessSessionToken = request.cookies.get('CloudPCAccessSessionToken')

    if CloudPCAccessSessionToken in ACCESSTOKENLIST:
        socket_id = request.sid  # Capturar el socket_id del cliente que se está conectando
        SOCKETIDLIST.append(socket_id)
    if not thread.is_alive():
        thread = Thread(target=capture_and_send_screen)
        thread.start()


@socketio.on('disconnect')
def on_disconnect():
    global SOCKETIDLIST, ACCESSTOKENLIST
    print('Client disconnected')

@socketio.on('mouse_move')
def handle_mouse_move(data):
    if request.sid in SOCKETIDLIST:
        try:
            pyautogui.moveTo(data['x'], data['y'])
        except pyautogui.FailSafeException:
            print("Fail-safe triggered. Mouse moved to a corner of the screen.")
            
@socketio.on('mouse_click')
def handle_mouse_click(data):
    if request.sid in SOCKETIDLIST:
        pyautogui.click(button=data['button'])

@socketio.on('mouse_scroll')
def handle_mouse_scroll(data):
    if request.sid in SOCKETIDLIST:
        pyautogui.scroll(int(data['deltaY']))

@socketio.on('key_press')
def handle_key_press(data):
    if request.sid in SOCKETIDLIST:
        #print(data['key'])
        pyautogui.press(data['key'])

@socketio.on('combination_key_press')
def press_key_combination(data):
    if request.sid in SOCKETIDLIST:
        # Dividir la cadena de la combinación en partes para usar con pyautogui.hotkey()
        #print(data['combination'])
        keys = data['combination'].split('+')
        # Simula la pulsación de la combinación de teclas
        pyautogui.hotkey(*keys)

def verificar_credenciales(usuario, contrasena):
    hashed_password = get_hashed_password(usuario)
    # Abrir el archivo en modo de lectura
    if hashed_password==None:
        return False
    elif hashed_password and bcrypt.checkpw(contrasena.encode('utf-8'), hashed_password):
        return True
    else:
        return False

@app.route('/')
def index():
    return render_template('startindex.html')

@app.route('/login', methods=['POST'])
def login():
    global ACCESSTOKENLIST, LASTTIMETOKENGENERATED
    usuario = request.form['username']
    contrasena = request.form['password']

    if verificar_credenciales(usuario, contrasena):
        accesstoken= secrets.token_urlsafe(LONGITUD)
        LASTTIMETOKENGENERATED=time.time()
        ACCESSTOKENLIST.append(accesstoken)
        response = make_response(jsonify({
            "redirect_show": "/show",
            "redirect_config": "/config"
        }))
        response.set_cookie('CloudPCAccessSessionToken', accesstoken, max_age=TOKENRESETTIME)  # Expira en 1 hora
        return response
    else:
        return jsonify({"error": "Credenciales inválidas"}), 401

@app.route('/logout', methods=['POST'])
def logout():
    global SOCKETIDLIST, ACCESSTOKENLIST
    usuario = request.form['username']
    contrasena = request.form['password']
    if verificar_credenciales(usuario, contrasena):
        SOCKETIDLIST.clear()
        ACCESSTOKENLIST.clear()
        response = make_response(jsonify({"message": "Sesión cerrada exitosamente"}))
        return response
    return jsonify({"error": "Credenciales inválidas"}), 401



def is_int(s):
    """ Helper function to check if a string can be converted to an integer. """
    try:
        int(s)
        return True
    except ValueError:
        return False

def is_float(s):
    """ Helper function to check if a string can be converted to a float. """
    try:
        float(s)
        return True
    except ValueError:
        return False

@app.route('/config', methods=['GET', 'POST'])
def index_config():
    global FRAMEQUALITY, FRAMEUPDATE, ACCESSTOKENLIST
    CloudPCAccessSessionToken = request.cookies.get('CloudPCAccessSessionToken')
    # print(CloudPCAccessSessionToken)
    if CloudPCAccessSessionToken in ACCESSTOKENLIST:
        if request.method == 'POST':
            frame_quality = request.form.get('frameQuality', '50')
            frame_update = request.form.get('updateRate', '1.0')

            try:
                if is_int(frame_quality) and is_float(frame_update):
                    if int(frame_quality)>100:
                        frame_quality=100
                    elif int(frame_quality)<1:
                        frame_quality=1
                    if float(frame_update)>1:
                        frame_update=1
                    elif float(frame_update)<0.001:
                        frame_update=0.001
                    with open(FRAME_QUALITY_FILE, 'w') as file:
                        json.dump(int(frame_quality), file)
                    with open(FRAME_UPDATE_FILE, 'w') as file:
                        json.dump(float(frame_update), file)
                    FRAMEQUALITY = int(frame_quality)
                    FRAMEUPDATE = float(frame_update)
                else:
                    print("Invalid input: frame_quality must be an integer and frame_update must be a float.")
            except Exception as e:
                print(f"An unexpected error occurred: {e}")

        with open('savedata/frameQuality.json', 'r') as archivo:
            frame_quality = json.load(archivo)  # Carga los datos del archivo
        with open('savedata/frameUpdate.json', 'r') as archivo:
            frame_update = json.load(archivo)  # Carga los datos del archivo
        frame_update = '{:.3f}'.format(frame_update).rstrip('0').rstrip('.')
        return render_template('serverconfig.html', frame_quality=frame_quality, frame_update=frame_update)
    else:
        return "Access Denied or Token Expired", 403

def get_host_ip():
    try:
        # Crea un socket DGRAM (UDP) para conectarse a un host de Internet
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            # No es necesario establecer una conexión real
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        print("Ocurrio un error")#return "127.0.0.1"  # En caso de fallo, retorna localhost

def read_port_from_file(file_path):
    """Lee el número de puerto desde un archivo dado."""
    try:
        with open(file_path, 'r') as file:
            port = file.read().strip()
            return int(port)
    except FileNotFoundError:
        print(f"El archivo {file_path} no se encuentra.")
    except ValueError:
        print(f"El contenido de {file_path} no es un número válido.")
    return None

def find_process_using_port(port):
    """Encuentra el PID de procesos utilizando el puerto especificado en Windows."""
    result = subprocess.run(['netstat', '-aon'], capture_output=True, text=True)
    lines = result.stdout.split("\n")
    pid = None
    for line in lines:
        if f':{port}' in line:
            parts = re.split(r'\s+', line)
            pid = parts[-1]
            break
    return pid

def kill_process(pid):
    """Termina el proceso con el PID especificado."""
    if pid:
        subprocess.run(['taskkill', '/F', '/PID', pid], capture_output=True)
        print(f"Proceso {pid} terminado.")
    else:
        print("No se encontró el proceso.")

if __name__ == '__main__':
    # Inicia el hilo de verificación antes de arrancar el servidor
    host_ip = get_host_ip()
    # Ruta al archivo
    file_path = 'savedata/serverConfig.txt'

    # Intentar leer el contenido del archivo y mostrarlo
    try:
        with open(file_path, 'r') as file:
            port = int(file.read().strip())  # Elimina espacios y saltos de línea al principio y al final
    except FileNotFoundError:
        print("El archivo 'serverConfig.txt' no se encuentra.")

    #port=443
    # port = 88#find_free_port()#88


    #app.run(host='0.0.0.0', port=443, ssl_context=('certificate.pem', 'private_key.pem'))


    HttpInsteadHttps=True

    print(f"Intentando liberar el puerto {port}...")
    pid = find_process_using_port(port)
    if pid:
        print(f"Encontrado proceso {pid} usando el puerto {port}, terminando proceso...")
        kill_process(pid)
    else:
        print(f"No se encontraron procesos utilizando el puerto {port}.")

    if HttpInsteadHttps:
        print(f"Servidor CloudPC ejecutándose en: http://{host_ip}:{port}")
        socketio.run(app, host='0.0.0.0', port=port)
    else:
        print(f"Servidor CloudPC ejecutándose en: https://{host_ip}:{port}")
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain('certificate.pem', 'private_key.pem')
        ssl_context.options |= ssl.OP_NO_SSLv2
        ssl_context.options |= ssl.OP_NO_SSLv3  # Deshabilita SSLv3 para mejorar la seguridad

        socketio.run(app, host='0.0.0.0', port=port, ssl_context=ssl_context)
