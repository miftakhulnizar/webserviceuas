# ============================
# 6D/19090081/Miftakhul Nizar
# 6D/19090128/Annon Pri Antomo
# ============================

import json
import pymongo
from bson.objectid import ObjectId
import os
import random
import string
import sys
import numpy as np
from util import base64_to_pil
from flask import Flask, redirect, url_for, request, Response, jsonify, session
from werkzeug.utils import secure_filename
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.applications.imagenet_utils import preprocess_input, decode_predictions
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tensorflow.keras.utils import get_file


app = Flask(__name__)

app.secret_key = 'sayuran'

# ========== SETUP MONGODB ==========
try:
    mongo = pymongo.MongoClient(
        host="localhost",
        port=27017,
        serverSelectionTimeoutMS=1000
    )
    db = mongo.vegetable
    mongo.server_info()
except:
    print("ERROR Connect To Database")




# ========== PREDICT ==========
model = load_model('models/model_vegetable.h5')


def model_predict(img, model):
    img = img.resize((224, 224))
    x = image.img_to_array(img)
    x = x.reshape(-1, 224, 224, 3)
    x = x.astype('float32')
    x = x / 255.0
    preds = model.predict(x)
    return preds


@app.route('/predict', methods=['POST'])
def predict():
    try:
        
        img = base64_to_pil(request.json)
        img.save("uploads/vege.png")
        preds = model_predict(img, model)
        target_names = [
            "Bean","Bitter_Gourd", "Bottle_Gourd", "Brinjal","Broccoli","Cabbage", "Capsicum" ,"Carrot", "Cauliflower", "Cucumber", "Papaya", "Potato", "Pumpkin", "Radish", "Tomato"
        ]

        hasil_label = target_names[np.argmax(preds)]
        data = list(db.informasi.find())

        for i, vege in enumerate(target_names):
            if hasil_label == vege:
                manfaat_tanaman = data[i]["manfaat"]

        hasil_prob = "{:.2f}".format(100 * np.max(preds))

        return jsonify(
            result=hasil_label,
            probability=hasil_prob + str('%'),
            manfaat=manfaat_tanaman
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Predict!"}),
            status=500,
            mimetype="application/json"
        )



# ========== CREATE USER ==========
@app.route("/users/create", methods=["POST"])
def create_user():
    try:
        user = {
            "username": request.json["username"],
            "password": request.json["password"],
            "token": request.json["token"]
        }
        dbResponse = db.users.insert_one(user)
        session['username'] = request.json["username"]
        return Response(
            response=json.dumps({
                "message": "User Created",
                "id": f"{dbResponse.inserted_id}"
            }),
            status=200,
            mimetype="application/json"
        )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Create User!"}),
            status=500,
            mimetype="application/json"
        )




# ========== LOGIN USER ==========
@app.route("/users/login", methods=["POST"])
def login_user():
    try:
        login_user = db.users.find_one({'username': request.form["username"]})
        if login_user:
            if request.form["password"] == login_user["password"]:
                db.users.update_one(
                    {"_id": login_user["_id"]},
                    {"$set": {
                        "token": ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                    }}
                )
                session["username"] = login_user["username"]
                return Response(
                    response=json.dumps({
                        "message": "Token Updated!"
                    }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({"message": "Password Salah!"}),
                    status=500,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({"message": "Username Salah!"}),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Login Gagal!"}),
            status=500,
            mimetype="application/json"
        )



# ========== CREATE vege ==========
@ app.route("/vege/create", methods=["POST"])
def create_vege():
    try:
        
        vege = {
            "nama": request.form["nama"],
            "manfaat": request.form["manfaat"]
        }
        dbResponse = db.informasi.insert_one(vege)
        # return redirect('/vege')
        return Response(
            response=json.dumps({
                "message": "vegetable Created",
                "id": f"{dbResponse.inserted_id}"
            }),
            status=200,
            mimetype="application/json"
        )
      
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Cannot Create vegetable!"}),
            status=500,
            mimetype="application/json"
        )

# =======================================


# ========== READ ==========
@ app.route("/vege", methods=["GET"])
def get_vege():
    try:
        if not session.get("username"):
            return redirect("/login")
       
        data = list(db.informasi.find())
        for vege in data:
            vege["_id"] = str(vege["_id"])
       
        return Response(
            response=json.dumps(data),
            status=200,
            mimetype="application/json"
        )
       
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({
                "message": "Cannot Get vegetable!"
            }),
            status=500,
            mimetype="application/json"
        )


# ========== UPDATE ==========
@ app.route("/vegetable/update/<id>", methods=["PUT"])
def update_vege(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.informasi.update_one(
                {"_id": ObjectId(id)},
                {"$set": {
                    "nama": request.json["nama"],
                    "manfaat": request.json["manfaat"]
                }}
            )
            if dbResponse.modified_count == 1:
                return Response(
                    response=json.dumps({"message": "vegetable Updated"}),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({"message": "Nothing To Update"}),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Sorry Cannot Update!"}),
            status=500,
            mimetype="application/json"
        )



# ========== DELETE ==========
@ app.route("/vegetable/delete/<id>", methods=["DELETE"])
def delete_vege(id):
    try:
        token = db.users.find_one({"token": request.json["token"]})
        if token:
            dbResponse = db.informasi.delete_one({"_id": ObjectId(id)})
            if dbResponse.deleted_count == 1:
                return Response(
                    response=json.dumps({
                        "message": "vegetable Deleted",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
            else:
                return Response(
                    response=json.dumps({
                        "message": "Plant Not Found",
                        "id": f"{id}"
                    }),
                    status=200,
                    mimetype="application/json"
                )
        else:
            return Response(
                response=json.dumps({
                    "message": "Token Salah!"
                }),
                status=500,
                mimetype="application/json"
            )
    except Exception as ex:
        print(ex)
        return Response(
            response=json.dumps({"message": "Sorry Cannot Delete!"}),
            status=500,
            mimetype="application/json"
        )



if __name__ == "__main__":
    app.run(port=8000, debug=True)
