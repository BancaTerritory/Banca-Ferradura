import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) # DON'T CHANGE THIS !!!

from flask import Blueprint, render_template, session

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    # The users_db is not directly accessible here for credits, session should be used
    return render_template("index.html")

