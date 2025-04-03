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
from functools import wraps
import time

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

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")

        # Token kontrolü
        if not token or not token.startswith("Bearer fake-token-"):
            return jsonify({"message": "Invalid Token"}), 403

        return f(*args, **kwargs)

    return decorated

USERS = [
    {"username": "admin", "password": "admin", "role": "admin"},
    {"username": "user", "password": "user", "role": "user"}
]

@app.route("/api/login", methods=["POST"])
@cross_origin()
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    # Find user
    user = next((u for u in USERS if u["username"] == username and u["password"] == password), None)

    if not user:
        return jsonify({"message": "Wrong username or password"}), 401

    # Create fake token
    token = f"fake-token-{int(time.time())}"

    return jsonify({"token": token, "role": user["role"]})


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
@token_required
def connect():
    try:
        role = request.headers.get("role")
        data = request.get_json()
        projectId = data.get("projectId")
        theme = data.get("theme")
        themeOverride = data.get("themeOverride")
        featureFlags = {
            "createDataInPeaka": False
        }
        if role == "user":
            featureFlags["queries"] = False
        else:
            featureFlags["queries"] = True
        
        headers = {
            "Authorization": f"Bearer {PEAKA_PARTNER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "timeoutInSeconds": 300,
            "projectId": projectId,
            "theme": "dark",
            "themeOverride": False,
            "featureFlags": {
                "createDataInPeaka": True,
                "queries": False
            }
        }

        # Get session url from partner api
        r = requests.post(
            f"{PEAKA_PARTNER_API_BASE_URL}/ui/initSession",
            json={
                "theme": theme,
                "themeOverride": themeOverride,
                "projectId": projectId,
                "featureFlags": featureFlags
            },
            headers=headers,
            json=payload,
        )
        response = r.json()
        session_url = response["sessionUrl"]

        return jsonify(sessionUrl=session_url, partnerOrigin=response["partnerOrigin"])
    except Exception as e:
        return f"There was an issue when connecting peaka. {e}"


@app.route("/get-data", methods=["POST"])
@cross_origin()
def get_data():
    try:
        api_key = request.json.get("apiKey", None)
        catalog_name = request.json.get("catalogName", None)
        schema_name = request.json.get("schemaName", None)
        table_name = request.json.get("tableName", None)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Get SQLAlchemy connection string from partner api
        r = requests.get(
            f"{PEAKA_PARTNER_API_BASE_URL}/supportedDrivers/sql_alchemy?catalogName={catalog_name}",
            headers=headers,
        )
        response = r.json()

        connection_string = response["SQL_ALCHEMY"]

        engine = create_engine(connection_string)
        connection = engine.connect()

        nodes = Table(
            table_name,
            MetaData(schema=schema_name),
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
