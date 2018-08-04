
from flask import Flask, request
import pinar as pn
print("Loading pinar")
pn_db = pn.Database()
pn_db.load("data/img_db.dat")
print("pinar loaded")
app = Flask(__name__)

@app.route('/')
def homepage():
    return "Hello"

@app.route('/images')
def images():
    ids = request.args.get("ids")
    ids = ids.split(" ")
    ids = [int(id) for id in ids]
    query = request.args.get("query")
    return str(ids + [query])


app.run(debug=True, port=5001)