import os
import re
from flask import Flask, jsonify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "CURSOS_CTPI_2026-CAROLINA")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "APRENDICES_MARRUGO")
PORT = int(os.getenv("PORT", 8000))

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
aprendices = db[COLLECTION_NAME]


# 10.1. Consultar la cantidad de aprendices
@app.route("/api/cantidadAprendices", methods=["GET"])
def cantidad_aprendices():
    cantidad = aprendices.count_documents({})
    return jsonify({"CantidadAprendices": cantidad})


# 10.2. Cantidad de aprendices por nivel de formación
@app.route("/api/cantidadAprendices/<nivel>", methods=["GET"])
def cantidad_por_nivel(nivel):
    nivel_limpio = nivel.strip()
    filtro = {
        "NIVEL_DE_FORMACION": {
            "$regex": f"^{re.escape(nivel_limpio)}$",
            "$options": "i",
        }
    }
    cantidad = aprendices.count_documents(filtro)

    ejemplo = aprendices.find_one(filtro, {"NIVEL_DE_FORMACION": 1, "_id": 0})
    nivel_respuesta = (
        ejemplo["NIVEL_DE_FORMACION"]
        if ejemplo and "NIVEL_DE_FORMACION" in ejemplo
        else nivel_limpio
    )

    return jsonify(
        {
            "CantidadAprendices": cantidad,
            "Nivel de formación": nivel_respuesta,
        }
    )


# 10.3. Listar programas únicos según el nivel de formación
@app.route("/api/programas/<nivel>", methods=["GET"])
def programas_por_nivel(nivel):
    nivel_limpio = nivel.strip()
    filtro = {
        "NIVEL_DE_FORMACION": {
            "$regex": f"^{re.escape(nivel_limpio)}$",
            "$options": "i",
        },
        "PROGRAMA": {"$ne": None},
    }
    programas = aprendices.distinct("PROGRAMA", filtro)
    programas_ordenados = sorted(
        [p.strip() for p in programas if isinstance(p, str) and p.strip()]
    )
    ejemplo = aprendices.find_one(filtro, {"NIVEL_DE_FORMACION": 1, "_id": 0})
    nivel_respuesta = (
        ejemplo["NIVEL_DE_FORMACION"]
        if ejemplo and "NIVEL_DE_FORMACION" in ejemplo
        else nivel_limpio
    )
    return jsonify(
        {
            "nivel de formación": nivel_respuesta,
            "programas": programas_ordenados,
        }
    )
    # 10.4. Aprendices certificados por programa (sin _id)
@app.route("/api/certificados/<programa>", methods=["GET"])
def aprendices_certificados(programa):
    programa_limpio = programa.strip()
    filtro = {
        "PROGRAMA": {
            "$regex": f"^{re.escape(programa_limpio)}$",
            "$options": "i",
        },
        "ESTADO_APRENDIZ": {
            "$regex": "^Certificado$",
            "$options": "i",
        },
    }
    proyeccion = {
        "_id": 0,
        "FICHA": 1,
        "NOMBRE": 1,
        "PRIMER_APELLIDO": 1,
        "SEGUNDO_APELLIDO": 1,
    }

    lista_aprendices = list(aprendices.find(filtro, proyeccion))
    ejemplo = aprendices.find_one(
        {"PROGRAMA": filtro["PROGRAMA"]}, {"PROGRAMA": 1, "_id": 0}
    )
    programa_respuesta = (
        ejemplo["PROGRAMA"]
        if ejemplo and "PROGRAMA" in ejemplo
        else programa_limpio
    )

    return jsonify(
        {
            "Aprendices_Certificados": lista_aprendices,
            "Programa": programa_respuesta,
        }
    )
 # 10.5. Aprendices por ficha en estado "Por certificar", ordenados desc por apellido, con límite
@app.route("/api/porCertificar/<ficha>/<int:limite>", methods=["GET"])
def aprendices_por_certificar(ficha, limite):
    ficha_limpia = ficha.strip()
    filtro_ficha = (
        {"$in": [int(ficha_limpia), ficha_limpia]}
        if ficha_limpia.isdigit()
        else ficha_limpia
    )

    filtro = {
        "FICHA": filtro_ficha,
        "ESTADO_APRENDIZ": {
            "$regex": "^Por certificar$",
            "$options": "i",
        },
    }

    proyeccion = {
        "_id": 0,
        "FICHA": 1,
        "PROGRAMA": 1,
        "NUMERO_DOCUMENTO": 1,
        "IDENTIFICACION": 1,
        "NOMBRE": 1,
        "PRIMER_APELLIDO": 1,
        "SEGUNDO_APELLIDO": 1,
    }

    resultados = list(
        aprendices.find(filtro, proyeccion)
        .sort("PRIMER_APELLIDO", -1)
        .limit(limite)
    )

    return jsonify({"Cantidad de Aprendices por Certificar": resultados})
# 10.6. Consultar fichas/aprendices por ESTADO_FICHA (ej. "Terminada por unificación")
@app.route("/api/estadoFicha/<estado>", methods=["GET"])
def fichas_por_estado(estado):
    estado_limpio = estado.strip()
    filtro = {
        "ESTADO_FICHA": {
            "$regex": f"^{re.escape(estado_limpio)}$",
            "$options": "i",
        }
    }

    fichas_unicas = sorted(
        [
            f
            for f in aprendices.distinct("FICHA", filtro)
            if f is not None and str(f).strip() != ""
        ],
        key=lambda x: str(x),
    )

    proyeccion = {
        "_id": 0,
        "FICHA": 1,
        "ESTADO_FICHA": 1,
        "PROGRAMA": 1,
        "NIVEL_DE_FORMACION": 1,
        "NUMERO_DOCUMENTO": 1,
        "NOMBRE": 1,
        "PRIMER_APELLIDO": 1,
        "SEGUNDO_APELLIDO": 1,
    }

    lista_aprendices = list(aprendices.find(filtro, proyeccion))
    ejemplo = aprendices.find_one(filtro, {"ESTADO_FICHA": 1, "_id": 0})
    estado_respuesta = (
        ejemplo["ESTADO_FICHA"]
        if ejemplo and "ESTADO_FICHA" in ejemplo
        else estado_limpio
    )

    return jsonify(
        {
            "Estado_Ficha": estado_respuesta,
            "Total_Fichas": len(fichas_unicas),
            "Fichas": fichas_unicas,
            "Total_Registros": len(lista_aprendices),
            "Registros": lista_aprendices,
        }
    )

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, port=PORT)