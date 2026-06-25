from flask import Flask
from flask import render_template
from flask import request
from flask import redirect
from flask import session
import os
from datetime import datetime
from supabase import create_client
from flask import flash


app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

app.secret_key = "newspreps-secret-key"


USERNAME = "venkat"
PASSWORD = "12345"



@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == USERNAME and password == PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if not session.get("logged_in"):
        return redirect("/")

    return render_template("dashboard.html")




@app.route("/search", methods=["GET", "POST"])
def search():

    if not session.get("logged_in"):
        return redirect("/")

    if request.method == "POST":

        selected_date = request.form["newspaper_date"]

        selected_date = datetime.strptime(
            selected_date,
            "%Y-%m-%d"
        ).date()

        response = supabase.table(
           "newspapers"
       ).select("*").eq(
           "newspaper_date",
           str(selected_date)
       ).execute()

        if response.data:
           newspaper = response.data[0]

           return render_template(
        "result.html",
        newspaper=newspaper
    )

        return render_template("not_found.html")

    return render_template("search.html")


@app.route("/upload", methods=["GET", "POST"])
def upload():

    if not session.get("logged_in"):
        return redirect("/")

    if request.method == "POST":

        pdf_file = request.files["pdf_file"]

        selected_date = request.form["newspaper_date"]
        response = supabase.table(
    "newspapers"
).select("*").eq(
    "newspaper_date",
    selected_date
).execute()
        if response.data:
            return "Newspaper already exists for this date."
        filename = f"{selected_date}.pdf"

        supabase.storage.from_("newspapers").upload(
    filename,
    pdf_file.read(),
    {
        "content-type": "application/pdf"
    }
)
        public_url = supabase.storage.from_(
            "newspapers"
        ).get_public_url(filename)
        supabase.table(
    "newspapers"
).insert({
    "newspaper_date": selected_date,
    "pdf_url": public_url
}).execute()
        
        flash("Newspaper uploaded successfully!")
        return redirect("/dashboard")
    
    return render_template("upload.html")




@app.route(
    "/delete-newspaper/<int:newspaper_id>",
    methods=["POST"]
)
def delete_newspaper(newspaper_id):

    if not session.get("logged_in"):
        return redirect("/")

    response = supabase.table(
        "newspapers"
    ).select("*").eq(
        "id",
        newspaper_id
    ).execute()
    
    if not response.data:
        flash("Newspaper not found!")
        return redirect("/dashboard")
    
    newspaper = response.data[0]


    filename = f"{newspaper['newspaper_date']}.pdf"

    supabase.storage.from_(
        "newspapers"
    ).remove([filename])

    supabase.table(
        "newspapers"
    ).delete().eq(
        "id",
        newspaper_id
    ).execute()

    flash("Newspaper deleted successfully!")

    return redirect("/dashboard")

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)