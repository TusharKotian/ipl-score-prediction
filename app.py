from flask import Flask, render_template, redirect, session, url_for, flash, request
import httpx
import pickle
import pandas as pd
import numpy as np
from supabase_config import supabase
from hashlib import sha256


app = Flask(__name__)
app.secret_key = "1234"


def hash_password(password):
    return sha256(password.encode()).hexdigest()


def flash_supabase_error():
    flash(
        "Supabase is not reachable. Check your internet connection and Supabase Project URL.",
        "error",
    )


# loading the model
with open("ipl.pkl", "rb") as f:
    model = pickle.load(f)


# Prediction function
def predict_score(
    bat_team="Mumbai Indians",
    bowl_team="Chennai Super Kings",
    runs=170,
    wickets=7,
    overs=6.2,
    runs_last_5=33,
    wickets_last_5=1,
):
    temp_array = list()
    if bat_team == "Chennai Super Kings":
        temp_array = temp_array + [1, 0, 0, 0, 0, 0, 0, 0]
    elif bat_team == "Delhi Daredevils":
        temp_array = temp_array + [0, 1, 0, 0, 0, 0, 0, 0]
    elif bat_team == "Kings XI Punjab":
        temp_array = temp_array + [0, 0, 1, 0, 0, 0, 0, 0]
    elif bat_team == "Kolkata Knight Riders":
        temp_array = temp_array + [0, 0, 0, 1, 0, 0, 0, 0]
    elif bat_team == "Mumbai Indians":
        temp_array = temp_array + [0, 0, 0, 0, 1, 0, 0, 0]
    elif bat_team == "Rajasthan Royals":
        temp_array = temp_array + [0, 0, 0, 0, 0, 1, 0, 0]
    elif bat_team == "Royal Challengers Bangalore":
        temp_array = temp_array + [0, 0, 0, 0, 0, 0, 1, 0]
    elif bat_team == "Sunrisers Hyderabad":
        temp_array = temp_array + [0, 0, 0, 0, 0, 0, 0, 1]

    if bowl_team == "Chennai Super Kings":
        temp_array = temp_array + [1, 0, 0, 0, 0, 0, 0, 0]
    elif bowl_team == "Delhi Daredevils":
        temp_array = temp_array + [0, 1, 0, 0, 0, 0, 0, 0]
    elif bowl_team == "Kings XI Punjab":
        temp_array = temp_array + [0, 0, 1, 0, 0, 0, 0, 0]
    elif bowl_team == "Kolkata Knight Riders":
        temp_array = temp_array + [0, 0, 0, 1, 0, 0, 0, 0]
    elif bowl_team == "Mumbai Indians":
        temp_array = temp_array + [0, 0, 0, 0, 1, 0, 0, 0]
    elif bowl_team == "Rajasthan Royals":
        temp_array = temp_array + [0, 0, 0, 0, 0, 1, 0, 0]
    elif bowl_team == "Royal Challengers Bangalore":
        temp_array = temp_array + [0, 0, 0, 0, 0, 0, 1, 0]
    elif bowl_team == "Sunrisers Hyderabad":
        temp_array = temp_array + [0, 0, 0, 0, 0, 0, 0, 1]
    temp_array = temp_array + [runs, wickets, overs, runs_last_5, wickets_last_5]

    temp_array = np.array([temp_array])
    return int(model.predict(temp_array)[0])


@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("index"))
    return redirect(url_for("login"))


@app.route("/index")
def index():
    if not session.get("user_id"):
        session.clear()
        return redirect(url_for("login"))
    return render_template("index.html")


@app.route("/predict", methods=["POST", "GET"])
def predict():

    if request.method == "POST":
        bat_team = request.form.get("batting_team", "Mumbai Indians")
        bowl_team = request.form.get("bowling_team", "Chennai Super Kings")

        runs = int(request.form.get("runs", 0))
        wickets = int(request.form.get("wickets", 0))
        overs = float(request.form.get("overs", 0))
        runs_last_5 = int(request.form.get("runs_last_5", 0))
        wickets_last_5 = int(request.form.get("wickets_last_5", 0))

        score = predict_score(
            bat_team, bowl_team, runs, wickets, overs, runs_last_5, wickets_last_5
        )

        return render_template("predict.html", prediction=score)

    return render_template("predict.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            existing = supabase.table("users").select("*").eq("email", email).execute()
        except (httpx.HTTPError, Exception):
            flash_supabase_error()
            return redirect(url_for("register"))

        if existing.data:
            flash("Email already registered. Please log in.", "error")
            return redirect(url_for("login"))

        hashed_password = hash_password(password)
        try:
            supabase.table("users").insert(
                {"uname": name, "email": email, "password": hashed_password}
            ).execute()
        except (httpx.HTTPError, Exception):
            flash_supabase_error()
            return redirect(url_for("register"))

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        try:
            response = supabase.table("users").select("*").eq("email", email).execute()
        except (httpx.HTTPError, Exception):
            flash_supabase_error()
            return redirect(url_for("login"))

        data = response.data

        if not data or not isinstance(data[0], dict):
            flash("Email not found. Please register first.", "error")
            return redirect(url_for("login"))

        user = data[0]
        stored_password = user.get("password")

        if stored_password is None:
            flash("User record is invalid.", "error")
            return redirect(url_for("login"))

        if hash_password(password) == stored_password:
            user_id = user.get("u_id") or user.get("id") or user.get("email")

            if not user_id:
                flash("User ID not found. Please contact support.", "error")
                return redirect(url_for("login"))

            session["user_id"] = user_id
            session["user_name"] = user.get("uname")
            session["user_email"] = user.get("email")
            flash("Login successful!", "success")
            return redirect(url_for("index"))

        flash("Incorrect password. Please try again.", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


if __name__ == "__main__":
    app.run(debug=True, port=4007,host='0.0.0.0')
