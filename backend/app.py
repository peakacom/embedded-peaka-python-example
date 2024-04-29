import json
import random, string
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import os
import requests
from sqlalchemy import create_engine
from sqlalchemy.schema import Table, MetaData
from sqlalchemy.sql.expression import select

load_dotenv()

app = Flask(__name__)
cors = CORS(app)
app.config["CORS_HEADERS"] = "Content-Type"

# Reading base url and partner api key from environment variable
PEAKA_PARTNER_API_BASE_URL = os.getenv("PEAKA_PARTNER_API_BASE_URL")
PEAKA_PARTNER_API_KEY = os.getenv("PEAKA_PARTNER_API_KEY")
auth_header = {
    "Authorization": f"Bearer {PEAKA_PARTNER_API_KEY}",
    "Content-Type": "application/json",
}


@app.route("/create-peaka-project", methods=["GET"])
@cross_origin()
def create_peaka_project():
    try:
        project_name = id_generator()

        # Create project by calling create project endpoint from partner api
        r = requests.post(
            f"{PEAKA_PARTNER_API_BASE_URL}/projects",
            json={"name": project_name},
            headers=auth_header,
        )

        response = r.json()
        peaka_project_id = response["id"]

        # Create project API Key by calling create API Key endpoint from partner api
        r = requests.post(
            f"{PEAKA_PARTNER_API_BASE_URL}/projects/{peaka_project_id}/apiKeys",
            json={
                "name": project_name,
            },
            headers=auth_header,
        )

        response = r.json()
        api_key = response["apiKey"]

        return jsonify(
            projectName=project_name, projectId=peaka_project_id, projectApiKey=api_key
        )
    except:
        return "There was an issue when creating peaka project."


@app.route("/connect", methods=["POST"])
@cross_origin()
def connect():
    try:
        apiKey = request.json.get("apiKey", None)

        headers = {
            "Authorization": f"Bearer {apiKey}",
            "Content-Type": "application/json",
        }

        # Get session url from partner api
        r = requests.get(
            f"{PEAKA_PARTNER_API_BASE_URL}/ui/initSession",
            headers=headers,
        )
        response = r.json()
        session_url = response["sessionUrl"]

        return jsonify(sessionUrl=session_url)
    except:
        return "There was an issue when connecting peaka."


@app.route("/get-data", methods=["POST"])
@cross_origin()
def get_data():
    try:
        apiKey = request.json.get("apiKey", None)
        catalogName = request.json.get("catalogName", None)
        schemaName = request.json.get("schemaName", None)
        tableName = request.json.get("tableName", None)

        headers = {
            "Authorization": f"Bearer {apiKey}",
            "Content-Type": "application/json",
        }

        # Get SQLAlchemy connection string from partner api
        r = requests.get(
            f"{PEAKA_PARTNER_API_BASE_URL}/supportedDrivers/sql_alchemy?catalogName={catalogName}",
            headers=headers,
        )
        response = r.json()

        connection_string = response["SQL_ALCHEMY"]

        engine = create_engine(connection_string)
        connection = engine.connect()

        nodes = Table(
            tableName,
            MetaData(schema=schemaName),
            peaka_autoload=True,
            autoload_with=engine,
        )

        # Fetch one row from table
        row = connection.execute(select(nodes)).fetchone()

        # Return 10 columns to client
        items = {}
        for index in range(10):
            items[nodes.columns[index].name] = row[index]

        return jsonify(items)
    except:
        return "There was an issue when getting data."


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return "".join(random.choice(chars) for _ in range(size))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=3001)
