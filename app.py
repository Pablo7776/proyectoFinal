from flask import Flask, jsonify, request, redirect, send_from_directory, render_template, url_for, session, flash

from flask_mysqldb import MySQL
from person import Person
from client import Client
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
from os import urandom


app = Flask(__name__)
CORS(app)


#Mysql Connection
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user_api_flask'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'db_api_flask'

"""La clave secreta es crucial en el manejo de sesiones y la seguridad en general en aplicaciones web. En Flask, se utiliza para firmar cookies y otros datos relacionados con la seguridad. La firma de cookies es un mecanismo que permite a la aplicación verificar la integridad de los datos almacenados en las cookies del usuario."""
app.config['SECRET_KEY'] = urandom(24)

mysql = MySQL(app)

# @app.route('/')
# def index():
#     #return jsonify({"massage": "API desarrollada con flask"})
#     #return redirect('/login.html')
#     return send_from_directory('.', 'login.html')


####################################################################################
def token_required(func): #chequeo!!!
    @wraps(func)
    def decorated(*args, **kwargs):
        print(kwargs)
        token = None

        if 'token' in session:  # Cambiado a buscar el token en la sesión de Flask
            token = session['token']

 
        if not token:
            return jsonify({
                "message": "Falta el token"
            }), 401
        


        user_id = None

        if 'user-id' in session:
            user_id = session['user-id']

        if not user_id:
            return jsonify({"message": "Falta el usuario"}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms = ['HS256'])

            token_id = data['id']



            if int(user_id) != int(token_id):
                return jsonify({"message": "Error de id"}), 401

        except Exception as e:
            print(e)
            return jsonify({"message": str(e)}), 401

        return func(*args, **kwargs)
    return decorated
####################################################################################


@app.route('/')

def home():
    # Aquí puedes verificar si el usuario está autenticado
    # Si no está autenticado, redirige a la página de login
    # Puedes implementar tu lógica de autenticación aquí

    # Por ahora, simplemente redirigimos a login.html para demostrar el concepto
    if 'token' not in session:
        return redirect(url_for('login'))

    # El usuario está autenticado, redirige a la página principal
    return redirect(url_for('index'))

# Ruta para el login
@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/process_login', methods = ['POST'])
def process_login():
    auth = request.authorization
    print(auth)

    """Control: existen valores para la autencicacion? """
    if not auth or not auth.username or not auth.password:
        return jsonify({"message": "no autorizado"}), 401
    
    """Control: existe y coincide el usuario en la BD? """
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM users WHERE username = %s AND password = %s', (auth.username, auth.password))
    row = cur.fetchone()

    if not row:
        return jsonify({"message": "no autorizado"}), 401
    
    """ El usuario existe en la BD y coincide su contraseña"""
    token = jwt.encode({'id': row[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=100)                 
                        
                        }, app.config['SECRET_KEY'])
    
    # Almacena el token en la sesión
    session['token'] = token
    session['user-id'] = str(row[0])

    return jsonify({"token": session['token'], "username": auth.username, "id": row[0]})





@app.route('/index')
@token_required #el que se identifica es el que generó el token
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client')
    data = cur.fetchall()
    #print(data)
    return render_template('index.html', contacts = data)




def client_resource(func): #chequeo!!!
    @wraps(func)
    def decorated(*args, **kwargs):
        print("Argumentos en client_resource: ", kwargs)
        id_cliente = kwargs['id_client']
        cur = mysql.connection.cursor()
        cur.execute('SELECT id_user FROM client WHERE id = {0}'.format(id_cliente))
        data = cur.fetchone()
        if data:
            
            """ print(data) """
            id_prop = data[0]
            user_id = request.headers['user-id'] #se supone que en este punto no debería generar problemas
            if int(id_prop) != int(user_id):
                return jsonify({"message": "No tiene permisos para acceder a este recurso"}), 401
        return func(*args, **kwargs)
    return decorated

def user_resources(func): #chequeo!!!
    @wraps(func)
    def decorated(*args, **kwargs):
        print("Argumentos en client_resources: ", kwargs)
        id_user_route = kwargs['id_user']
        
        user_id = request.headers['user-id'] #se supone que en este punto no debería generar problemas
        if int(id_user_route) != int(user_id):
            return jsonify({"message": "No tiene permisos para acceder a este recurso"}), 401
        return func(*args, **kwargs)
    return decorated




@app.route('/test/<int:id>')
@token_required
def test(id):
    return jsonify({"message": "funcion test"})


@app.route('/agregar_cliente', methods = ['POST'])
def agregar_cliente():
    if request.method == 'POST':
       nombre = request.form['nombre']
       id_user = 2 #despuesa cambiar por id del usuario

       cur = mysql.connection.cursor()
       cur.execute('INSERT INTO client (name, id_user) VALUES (%s,%s)', (nombre, id_user))
       mysql.connection.commit()
       flash('Contacto agregado satisfactoriamente')
       return redirect(url_for('index'))


@app.route('/borrar/<string:id>')
def borrar_cliente(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM client WHERE id = {0}'.format(id))
    mysql.connection.commit()
    flash('Cliente borrado')
    return redirect(url_for('index'))

@app.route('/editar/<id>')
def get_cliente(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client WHERE id = %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return render_template('editar-contactos.html', contact = data[0])


@app.route('/update/<id>', methods = ['POST'])
def update_contact(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        usuario = request.form['usuario']
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE client
            SET name = %s,
                id_user = %s
            WHERE id = %s
        """, (nombre, usuario, id))
        mysql.connection.commit()
        flash('contacto actualizado')
        return redirect(url_for('index'))



























@app.route('/persons', methods = ['GET'])
def get_all_persons():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM person')
    data = cur.fetchall()
    print(cur.rowcount)
    print(data)

    personList = []
    for row in data:
        objPerson = Person(row)
        personList.append(objPerson.to_json())
    return jsonify(personList)

""" @app.post('/persons') """
@app.route('/persons', methods = ['POST'])
def create_person():
    name = request.get_json()["name"]
    surname = request.get_json()["surname"]
    dni = request.get_json()["dni"]
    email = request.get_json()["email"]

    cur = mysql.connection.cursor()
    """Control si existe el email indicado"""

    cur.execute('SELECT * FROM person WHERE email = "{0}"'.format(email)) #el profe lo hace de otra manera , ver 1:54 clase 8
    row = cur.fetchone()

    if row:
        return jsonify({"message": "email ya registrado"})

    """ acceso a BD -> INSERT INTO """
    
    cur.execute("INSERT INTO person (name, surname, dni, email) VALUES (%s,%s,%s,%s)", (name, surname, dni, email))
    mysql.connection.commit()

    """ obtener el id del registro creado"""
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    print(row[0])
    id = row[0]

    return jsonify({"name": name, "surname": surname, "dni": dni, "email": email, "id": id })


@app.route('/cliente', methods = ['POST'])
def create_cliente():
    name = request.get_json()["name"]
    id_user = request.get_json()["id_user"]


    cur = mysql.connection.cursor()
    # """Control si existe el email indicado"""

    # cur.execute('SELECT * FROM client WHERE name = "{0}"'.format(name)) #el profe lo hace de otra manera , ver 1:54 clase 8
    # row = cur.fetchone()

    # if row:
    #     return jsonify({"message": "email ya registrado"})

    """ acceso a BD -> INSERT INTO """
    
    cur.execute("INSERT INTO client (name, id_user) VALUES (%s, %s)", (name , id_user))
    mysql.connection.commit()

    """ obtener el id del registro creado"""
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    print(row[0])
    id = row[0]

    return jsonify({"name": name, "id": id })



@app.route('/persons/<int:id>', methods = ['GET'])
def get_person_by_id(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM person WHERE id = {0}'.format(id))
    data = cur.fetchall()
    print(cur.rowcount)
    print(data)
    if cur.rowcount > 0:
        objPerson = Person(data[0])
        return jsonify(objPerson.to_json())
    return jsonify({"message": "id not found"})

@app.route('/person/<int:id>', methods = ['PUT'])
def uptate_person(id):
    name = request.get_json()["name"]
    surname = request.get_json()["surname"] 
    dni = request.get_json()["dni"]
    email = request.get_json()["email"]
    """ UPDATE SET ... WHERE ... """
    cur = mysql.connection.cursor()
    cur.execute('UPDATE person SET name = %s, surname = %s, dni = %s, email = %s WHERE id = %s', (name, surname, dni, email, id))
    mysql.connection.commit()
    return jsonify({ "id":id, "name": name, "surname": surname, "dni": dni, "email": email})


@app.route('/client/<int:id>', methods = ['PUT'])
def uptate_cliente(id):
    name = request.get_json()["name"]
    """ UPDATE SET ... WHERE ... """
    cur = mysql.connection.cursor()
    cur.execute('UPDATE client SET name = %s WHERE id = %s', (name, id))
    mysql.connection.commit()
    return jsonify({ "id":id, "name": name})

@app.route('/persons/<int:id>', methods = ['DELETE']) # Esto es un borrado físico, buscar el borrado lógico
def remove_person(id):
    """ DELETE FROM WHERE... """
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM person WHERE id = {0}'.format(id))
    mysql.connection.commit()
    return jsonify({"message": "deleted", "id":id})


#@app.route('/client/<int:id>', methods = ['GET'])
@app.route('/user/<int:id>/client/<int:id_client>', methods = ['GET']) #para identificar a un cliente primero tengo que tener a su usuario
@token_required #el que se identifica es el que generó el token
@user_resources #si me identifico como usuario 5 no puedo acceder a la rura de otro usuario
@client_resource #controla que <int:id_client> sea propiedad de <int:id>
def get_client_by_id(id_client):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client WHERE id = {0}'.format(id_client))
    data = cur.fetchall()
    print(cur.rowcount)
    print(data)
    if cur.rowcount > 0:
        objClient = Client(data[0])
        return jsonify(objClient.to_json())
    return jsonify({"message": "id not found"}), 404


@app.route('/user/<int:id_user>/client', methods = ['GET'])
@token_required
@user_resources # voy a poder ver a los clientes del usuaro 5 si ya tengo el token y me identifico como usuario 5
def get_all_clients_by_user_id(id_user):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client WHERE id_user = {0}'.format(id_user))
    data = cur.fetchall()
    ClientList = []
    for row in data:
        objClient = Client(row)
        ClientList.append(objClient.to_json())
        print(row)
    return jsonify(ClientList)













if __name__ == '__main__':
    app.run(debug=True, port=4500)




















if __name__ == '__main__':
    app.run(debug=True, port=5000)