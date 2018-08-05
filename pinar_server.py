
from flask import Flask, request
import pinar as pn
print("Loading pinar")
pn_db = pn.Database()
pn_db.load("data/img_db.dat")
print("pinar loaded")

with open("templates/header.html", 'rb') as f:
    header = f.read().decode("utf-8")
with open("templates/footer.html", 'rb') as f:
    footer = f.read().decode("utf-8")
with open("templates/image.html", 'rb') as f:
    body = f.read().decode("utf-8")

app = Flask(__name__)

@app.route('/')
def homepage():
    return "Hello"

def body_creation(ids):
    rethtml = ""
    urls = [pn_db.supplementary_information[id] for id in ids]
    for i in range(len(ids)):
        rethtml += body.format(ids[i], urls[i])
    return rethtml

@app.route('/search_by_text')
def images():
    query = request.args.get("query")
    print(query)
    ids = pn_db.match(query, 10)
    print(ids)
    rethtml = header.format("word", query)
    rethtml += body_creation(ids)
    rethtml += footer
    return rethtml

@app.route('/search_by_image')
def search_by_image():
    id = int(request.args.get("id"))
    ids = pn_db.similar(id, 10)

    rethtml = header.format("image id", id)
    rethtml += body_creation(ids)
    rethtml += footer
    return rethtml

app.run(debug=True, port=5001)