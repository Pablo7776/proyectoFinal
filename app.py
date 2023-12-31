from flask import Flask, jsonify, request, redirect, send_from_directory , url_for, session, flash

from flask_mysqldb import MySQL
from person import Person
from client import Client
from producto import Producto
import jwt
import datetime
from functools import wraps
from flask_cors import CORS
from os import urandom


app = Flask(__name__, static_folder='templates', static_url_path='')
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

#Ruta para el login
@app.route('/login', methods=['GET'])
def login():
    return send_from_directory(app.static_folder, 'login.html')


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
@token_required
def index():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client')
    data = cur.fetchall()

#   # Almacena los datos en la sesión
#     session['contacts'] = data

    # Redirigir a la página index.html
    return redirect(url_for('show_index_page'))

@app.route('/show_index_page')
def show_index_page():
        # Recupera los datos de la sesión
    # contacts = session.get('contacts', [])
    # print(contacts)

    # Aquí puedes agregar la lógica necesaria antes de renderizar la página
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/agregarCliente.html')
def agregar_nuevo_cliente():
    return send_from_directory(app.static_folder, 'agregarCliente.html')

@app.route('/mostrarListaClientes.html')
def mostrarListaClientes():
    return send_from_directory(app.static_folder, 'mostrarListaClientes.html')


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
def borrar_cliente2(id):
    cur = mysql.connection.cursor()
    cur.execute('DELETE FROM client WHERE id = {0}'.format(id))
    mysql.connection.commit()
    # flash('Cliente borrado')
    # return redirect(url_for('index'))

@app.route('/editar/<id>')
def get_cliente(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM client WHERE id = %s', (id,))
    data = cur.fetchall()
    print(data[0])
    return send_from_directory(app.static_folder, 'editar-contactos.html')


# @app.route('/update/<id>', methods = ['POST'])
# def update_contact(id):
#     if request.method == 'POST':
#         nombre = request.form['nombre']
#         usuario = request.form['usuario']
#         cur = mysql.connection.cursor()
#         cur.execute("""
#             UPDATE client
#             SET name = %s,
#                 id_user = %s
#             WHERE id = %s
#         """, (nombre, usuario, id))
#         mysql.connection.commit()
#         flash('contacto actualizado')
#         return redirect(url_for('index'))



























# @app.route('/persons', methods = ['GET'])
# def get_all_persons():
#     cur = mysql.connection.cursor()
#     cur.execute('SELECT * FROM person')
#     data = cur.fetchall()
#     print(cur.rowcount)
#     print(data)

#     personList = []
#     for row in data:
#         objPerson = Person(row)
#         personList.append(objPerson.to_json())
#     return jsonify(personList)

# """ @app.post('/persons') """
# @app.route('/persons', methods = ['POST'])
# def create_person():
#     name = request.get_json()["name"]
#     surname = request.get_json()["surname"]
#     dni = request.get_json()["dni"]
#     email = request.get_json()["email"]

#     cur = mysql.connection.cursor()
#     """Control si existe el email indicado"""

#     cur.execute('SELECT * FROM person WHERE email = "{0}"'.format(email)) #el profe lo hace de otra manera , ver 1:54 clase 8
#     row = cur.fetchone()

#     if row:
#         return jsonify({"message": "email ya registrado"})

#     """ acceso a BD -> INSERT INTO """
    
#     cur.execute("INSERT INTO person (name, surname, dni, email) VALUES (%s,%s,%s,%s)", (name, surname, dni, email))
#     mysql.connection.commit()

#     """ obtener el id del registro creado"""
#     cur.execute('SELECT LAST_INSERT_ID()')
#     row = cur.fetchone()
#     print(row[0])
#     id = row[0]

#     return jsonify({"name": name, "surname": surname, "dni": dni, "email": email, "id": id })


@app.route('/cliente', methods = ['POST'])
def create_cliente():
    name = request.get_json()["name"]
    id_user = request.get_json()["id_user"]


    cur = mysql.connection.cursor()
 

    """ acceso a BD -> INSERT INTO """
    
    cur.execute("INSERT INTO client (name, id_user) VALUES (%s, %s)", (name , id_user))
    mysql.connection.commit()

    """ obtener el id del registro creado"""
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    print(row[0])
    id = row[0]

    return jsonify({"name": name, "id": id })



# @app.route('/persons/<int:id>', methods = ['GET'])
# def get_person_by_id(id):
#     cur = mysql.connection.cursor()
#     cur.execute('SELECT * FROM person WHERE id = {0}'.format(id))
#     data = cur.fetchall()
#     print(cur.rowcount)
#     print(data)
#     if cur.rowcount > 0:
#         objPerson = Person(data[0])
#         return jsonify(objPerson.to_json())
#     return jsonify({"message": "id not found"})

# @app.route('/person/<int:id>', methods = ['PUT'])
# def uptate_person(id):
#     name = request.get_json()["name"]
#     surname = request.get_json()["surname"] 
#     dni = request.get_json()["dni"]
#     email = request.get_json()["email"]
#     """ UPDATE SET ... WHERE ... """
#     cur = mysql.connection.cursor()
#     cur.execute('UPDATE person SET name = %s, surname = %s, dni = %s, email = %s WHERE id = %s', (name, surname, dni, email, id))
#     mysql.connection.commit()
#     return jsonify({ "id":id, "name": name, "surname": surname, "dni": dni, "email": email})


@app.route('/client/<int:id>', methods = ['PUT'])
def uptate_cliente(id):
    name = request.get_json()["name"]
    """ UPDATE SET ... WHERE ... """
    cur = mysql.connection.cursor()
    cur.execute('UPDATE client SET name = %s WHERE id = %s', (name, id))
    mysql.connection.commit()
    return jsonify({ "id":id, "name": name})

@app.route('/borrar_cliente/<int:id>', methods = ['DELETE']) # Esto es un borrado físico, buscar el borrado lógico
@token_required #el que se identifica es el que generó el token
# @user_resources #si me identifico como usuario 5 no puedo acceder a la rura de otro usuario
# @client_resource #controla que <int:id_client> sea propiedad de <int:id>
def remove_person(id):
    """ DELETE FROM WHERE... """
    print(f"Delete request received for ID: {id}")
    cur = mysql.connection.cursor()
    try:
        cur.execute('DELETE FROM client WHERE id = {0}'.format(id))
        mysql.connection.commit()
        print(f"Delete successful for ID: {id}")
        return jsonify({"message": "deleted", "id": id}), 200
    except Exception as e:
        print(f"Error deleting record with ID {id}: {str(e)}")
        return jsonify({"message": "error", "error": str(e)}), 500


# #@app.route('/client/<int:id>', methods = ['GET'])
# @app.route('/user/<int:id>/client/<int:id_client>', methods = ['GET']) #para identificar a un cliente primero tengo que tener a su usuario
# @token_required #el que se identifica es el que generó el token
# @user_resources #si me identifico como usuario 5 no puedo acceder a la rura de otro usuario
# @client_resource #controla que <int:id_client> sea propiedad de <int:id>
# def get_client_by_id(id_client):
#     cur = mysql.connection.cursor()
#     cur.execute('SELECT * FROM client WHERE id = {0}'.format(id_client))
#     data = cur.fetchall()
#     print(cur.rowcount)
#     print(data)
#     if cur.rowcount > 0:
#         objClient = Client(data[0])
#         return jsonify(objClient.to_json())
#     return jsonify({"message": "id not found"}), 404


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






###################################################

@app.route('/crear_producto', methods = ['POST'])
def create_producto():
    
    producto = request.get_json()["producto"]
    cantidad = request.get_json()["cantidad"]
    precio = request.get_json()["precio"]
    id_user = request.get_json()["id_user"]



    cur = mysql.connection.cursor()
 

    """ acceso a BD -> INSERT INTO """
    
    cur.execute("INSERT INTO productos ( producto, cantidad, precio, id_user ) VALUES ( %s, %s, %s, %s)", ( producto, cantidad, precio, id_user))
    mysql.connection.commit()

    """ obtener el id del registro creado"""
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    print(row[0])
    id = row[0]

    return jsonify({"name": producto, "cantidad": cantidad , "precio": precio})


@app.route('/borrar_producto/<int:id>', methods = ['DELETE']) # Esto es un borrado físico, buscar el borrado lógico
@token_required #el que se identifica es el que generó el token
# @user_resources #si me identifico como usuario 5 no puedo acceder a la rura de otro usuario
# @client_resource #controla que <int:id_client> sea propiedad de <int:id>
def remove_person(id):
    """ DELETE FROM WHERE... """
    print(f"Delete request received for ID: {id}")
    cur = mysql.connection.cursor()
    try:
        cur.execute('DELETE FROM producto WHERE id = {0}'.format(id))
        mysql.connection.commit()
        print(f"Delete successful for ID: {id}")
        return jsonify({"message": "deleted", "id": id}), 200
    except Exception as e:
        print(f"Error deleting record with ID {id}: {str(e)}")
        return jsonify({"message": "error", "error": str(e)}), 500
    
@app.route('/producto/<int:id>', methods = ['PUT'])
def uptate_cliente(id):
    producto = request.get_json()["producto"]
    cantidad = request.get_json()["cantidad"]
    precio = request.get_json()["precio"]
    """ UPDATE SET ... WHERE ... """
    cur = mysql.connection.cursor()
    cur.execute('UPDATE producto SET producto = %s, cantidad = %s, precio = %s WHERE id = %s', (producto, cantidad, precio ,id))
    mysql.connection.commit()
    return jsonify({ "id":id, "name": producto})



@app.route('/user/<int:id_user>/producto', methods = ['GET'])
@token_required
@user_resources # voy a poder ver a los clientes del usuaro 5 si ya tengo el token y me identifico como usuario 5
def get_all_clients_by_user_id(id_user):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM producto WHERE id_user = {0}'.format(id_user))
    data = cur.fetchall()
    ProductoList = []
    for row in data:
        objClient = Client(row)
        ProductoList.append(objClient.to_json())
        print(row)
    return jsonify(ProductoList)


######################################################




@app.route('/crear_servicio', methods = ['POST'])
@token_required
@user_resources
def create_producto():
    
    servicio = request.get_json()["servicio"]
    precio = request.get_json()["precio"]
    id_user = request.get_json()["id_user"]



    cur = mysql.connection.cursor()
 

    """ acceso a BD -> INSERT INTO """
    
    cur.execute("INSERT INTO servicios ( servicio, precio, id_user ) VALUES ( %s, %s, %s)", ( servicio, precio, id_user))
    mysql.connection.commit()

    """ obtener el id del registro creado"""
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    print(row[0])
    id = row[0]

    return jsonify({"name": servicio, "precio": precio })



@app.route('/borrar_servicio/<int:id>', methods = ['DELETE']) # Esto es un borrado físico, buscar el borrado lógico
@token_required #el que se identifica es el que generó el token
# @user_resources #si me identifico como usuario 5 no puedo acceder a la rura de otro usuario
# @client_resource #controla que <int:id_client> sea propiedad de <int:id>
def remove_person(id):
    """ DELETE FROM WHERE... """
    print(f"Delete request received for ID: {id}")
    cur = mysql.connection.cursor()
    try:
        cur.execute('DELETE FROM servicios WHERE id = {0}'.format(id))
        mysql.connection.commit()
        print(f"Delete successful for ID: {id}")
        return jsonify({"message": "deleted", "id": id}), 200
    except Exception as e:
        print(f"Error deleting record with ID {id}: {str(e)}")
        return jsonify({"message": "error", "error": str(e)}), 500
    

@app.route('/servicios/<int:id>', methods = ['PUT'])
@token_required
@user_resources
def uptate_cliente(id):
    servicio = request.get_json()["producto"]
    precio = request.get_json()["precio"]
    """ UPDATE SET ... WHERE ... """
    cur = mysql.connection.cursor()
    cur.execute('UPDATE productos SET servicio = %s, precio = %s WHERE id = %s', (servicio, precio ,id))
    mysql.connection.commit()
    return jsonify({ "id":id, "name": servicio})
















if __name__ == '__main__':
    app.run(debug=True, port=4500)



@app.route('/user/<int:id_user>/servicios', methods = ['GET'])
@token_required
@user_resources # voy a poder ver a los clientes del usuaro 5 si ya tengo el token y me identifico como usuario 5
def get_all_clients_by_user_id(id_user):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM servicios WHERE id_user = {0}'.format(id_user))
    data = cur.fetchall()
    ServiciosList = []
    for row in data:
        objClient = Client(row)
        ServiciosList.append(objClient.to_json())
        print(row)
    return jsonify(ServiciosList)


###################################################


from flask import request, jsonify
@token_required
@user_resources
@app.route('/crear_factura', methods=['POST'])
def create_factura():
    data = request.get_json()

    if 'cliente_id' in data and 'items' in data:
        return create_factura_internal(data)
    else:
        return jsonify({"message": "Solicitud no válida"}), 400

def create_factura_internal(data):
    cliente_id = data["cliente_id"]
    items = data["items"]

    cur = mysql.connection.cursor()

    # Crear factura
    cur.execute("INSERT INTO factura (cliente_id) VALUES (%s)", (cliente_id,))
    mysql.connection.commit()

    # Obtener el ID de la factura recién creada
    cur.execute('SELECT LAST_INSERT_ID()')
    row = cur.fetchone()
    factura_id = row[0]

    # Agregar productos y servicios a la factura
    for item in items:
        if item["tipo"] == "producto":
            cur.execute("INSERT INTO factura_item (factura_id, tipo, producto_id, cantidad) VALUES (%s, %s, %s, %s)", (factura_id, item["tipo"], item["id"], item["cantidad"]))
        elif item["tipo"] == "servicio":
            cur.execute("INSERT INTO factura_item (factura_id, tipo, servicio_id, cantidad) VALUES (%s, %s, %s, %s)", (factura_id, item["tipo"], item["id"], item["cantidad"]))
        mysql.connection.commit()

    return jsonify({"factura_id": factura_id, "cliente_id": cliente_id, "items": items})



@app.route('/user/<int:id_user>/facturas', methods=['GET'])
@token_required
@user_resources
def get_all_facturas_by_user_id(id_user):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM factura WHERE cliente_id = %s', (id_user,))
    data = cur.fetchall()

    facturas_list = []
    for row in data:
        factura = {
            "factura_id": row[0],
            "cliente_id": row[1],
            # Agrega más propiedades según la estructura de tu tabla factura
        }
        facturas_list.append(factura)

    return jsonify({"facturas": facturas_list})














if __name__ == '__main__':
    app.run(debug=True, port=5000)