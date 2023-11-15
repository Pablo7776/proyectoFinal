from flask import Flask, jsonify, request
from markupsafe import escape

app = Flask(__name__)


@app.route('/')
def index():
    return 'Index'




@app.route('/ping')
def ping():
    return jsonify({"message": "pong"})



@app.route('/usuarios/<string:nombre>')
def usuario_by_name(nombre):
    return jsonify({"name": nombre})

@app.route('/usuariosX/<int:id>')
def usuario_by_id(id):
    return jsonify({"id": id})

@app.route('/<path:nombre>')
def no_hacer(nombre):
    return escape(nombre)


#GET todos los "recursos"
@app.route('/recurso', methods = ['GET'])
def get_recursos():
    return jsonify({"data": "lista de todos los items de este recurso"})




# POST nuevo 'recurso'
@app.route('/recurso', methods = ['POST'])
def post_recurso():
    print(request.get_json())
    body = request.get_json()
    name = body["name"]
    modelo = body["modelo"]
    # insertar en la BD
    return jsonify({"recurso": {
        "name": name,
        "modelo": modelo
    }})

@app.route('/recurso/<int:id>', methods = ['get'])
def get_recursos_by_id(id):
    #buscar en una base de datos un registro con ese id
    return jsonify({"recurso":{
        "name": "fsad",
        "modelos": "gfsadg" 
    }})

























if __name__ == '__main__':
    app.run(debug=True, port=5000)