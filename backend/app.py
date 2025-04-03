"""
This module implements a Flask API with authentication, 
Embedded Peaka session initialization, and utility functions.

Key features of the module:
1. **Login Endpoint (`/api/login`)**:
   - Accepts user credentials (username and password) and returns a fake authentication token 
     along with the user's role.
   - Used for basic authentication in the system.

2. **Connect Endpoint (`/connect`)**:
   - Requires a valid token to access.
   - Initializes a session with the Peaka partner API by sending a request with project and 
     theme settings, and feature flags.
   - Returns the session URL and partner origin.

3. **Utility Function (`id_generator`)**:
   - Generates a random ID of a specified length using a custom or default set of characters.

The module utilizes the `dotenv` library to load configuration values such as API keys and URLs 
from environment variables. The `CORS` headers are set up to allow cross-origin requests, 
and the `requests` library is used for external API calls.
"""

import random
from functools import wraps
import os
import time
import string
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import requests

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
    """
    Decorator to ensure that a valid token is provided in the request headers.

    This decorator checks if the request includes an `Authorization` header with a token that starts
    with the prefix `Bearer fake-token-`. If the token is missing or invalid, 
    the function will return a 403 error with a message `"Invalid Token"`. 
    If the token is valid, the decorated function will be executed.

    Args:
        f: The function to be decorated. It will only be executed if the token is valid.

    Returns:
        function: The decorated function. If the token is valid, the original function is called. 
        Otherwise, a 403 error response with the message `"Invalid Token"` is returned.

    Raises:
        None: This function does not raise any explicit exceptions.
    """
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
    """
    Handles the login process for users by verifying their username and password.

    This function accepts a POST request with the username and password, 
    searches for a matching user in the list of users, and returns a fake token 
    if the credentials are valid. The role of the user is also returned along 
    with the token. If the credentials are incorrect, a 401 error with a message is returned.

    Args:
        None: The function expects data in the request body (JSON format) containing:
            - `username`: The username of the user.
            - `password`: The password of the user.

    Returns:
        json: A JSON response containing:
            - `token`: A fake token generated for the authenticated user.
            - `role`: The role of the authenticated user.
        If authentication fails, a JSON response with an error message and status 
        code 401 is returned.

    Raises:
        None: The function does not raise any explicit exceptions.
    """
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


@app.route("/connect", methods=["POST"])
@cross_origin()
@token_required
def connect():
    """
    Establishes a connection to the Peaka partner API to initialize an Embedded Peaka Session.

    This function extracts data from the incoming request, including the user's role, project ID,
    theme settings, and feature flags. Based on the role, it determines which feature 
    flags are enabled. Then, it sends a request to the Peaka partner API to initiate a session 
    and retrieve the session URL.

    Args:
        None: The data is extracted from the incoming request.

    Returns:
        json: A JSON response containing the session URL and partner origin.

    Raises:
        Exception: If there is any issue during the connection process, an exception will be raised
        and a message will be returned indicating the failure.
    """
    try:
        role = request.headers.get("role")
        data = request.get_json()
        project_id = data.get("projectId")
        theme = data.get("theme")
        theme_override = data.get("themeOverride")
        feature_flags = {
            "createDataInPeaka": False
        }
        if role == "user":
            feature_flags["queries"] = False
        else:
            feature_flags["queries"] = True

        headers = {
            "Authorization": f"Bearer {PEAKA_PARTNER_API_KEY}",
            "Content-Type": "application/json",
        }

        # Get session url from partner api
        r = requests.post(
            f"{PEAKA_PARTNER_API_BASE_URL}/ui/initSession",
            json={
                "theme": theme,
                "themeOverride": theme_override,
                "projectId": project_id,
                "featureFlags": feature_flags
            },
            headers=headers,
            timeout=5
        )
        response = r.json()
        session_url = response["sessionUrl"]

        return jsonify(sessionUrl=session_url, partnerOrigin=response["partnerOrigin"])
    except Exception as e:
        return f"There was an issue when connecting peaka. {e}"


def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    """
    Generates a random ID.

    This function generates a random ID of the specified length, using the provided character set.
    By default, the ID consists of uppercase letters and digits, but the character set 
    can be customized.

    Args:
        size (int, optional): The length of the generated ID. Default is 6.
        chars (str, optional): The character set to choose from. By default, uppercase 
        letters and digits are used.

    Returns:
        str: A randomly generated ID of the specified length.
    """
    return "".join(random.choice(chars) for _ in range(size))


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=3001)
