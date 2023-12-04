class Producto():
    def __init__(self, row):
        self._id = row[0]
        self._producto = row[1]
        self._cantidad = row[2]
        self._id_user = row[3]


    def to_json(self):
        return{
            "id": self._id,
            "producto": self._producto,
            "cantidad": self._cantidad,
            "id_user": self._id_user,


        }