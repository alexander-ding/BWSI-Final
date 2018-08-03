import pooja as pj
import thorben as tb
import pinar as pn
from flask import Flask
from flask_ask import Ask, statement, question
from pathlib import Path

print("Loading pooja")
pj_db = pj.database()
pj_db.load("song_db.dat")
print("pooja loaded")

print("Loading thorben")
tb_db = tb.Database("face_db.dat")
print("thorben loaded")
space = " "
n = "and"

app = Flask(__name__)
ask = Ask(app, '/')

@app.route('/')
def homepage():
    return "Hello"

@ask.launch
def start_skill():
    print("Test")
    welcome_message = "Odin here. What do you want to do?" 
    return question(welcome_message)

@ask.intent("SongIntent")
def matching_song():
    print("GOT INTENT")
    aux = pj.input_mic(7)
    result = pj_db.match_song(aux)
    return question(result)

@ask.intent("FaceAddIntent")
def adding_face():
    print("Got intent")
    return question("Who is this?")
    
@ask.intent("NameIntent")    
def finding_face(name):
    identity = tb_db.add_user(name)
    for i in range(1,5):
        picture = tb.from_camera()
        tb_db.add_image(picture, identity)
    return question("Okay, I got you")

@ask.intent("FaceRecIntent")
def recognizing_face():
    print("Got intent")
    picture = tb.from_camera()
    who = tb_db.match(picture)
    vision = "I see"
    count = 0
    for iden in who:
        vision += space + iden
        count += 1
        if not count == len(who):
            vision += space + n
    return question(vision)

@ask.intent("KeywordIntent")
def keyword_imaging():
    print("I got it")
    return question("Function not implemented yet")

@ask.intent("AMAZON.FallbackIntent")
@ask.intent("AMAZON.StopIntent")
@ask.intent("AMAZON.CancelIntent")
def bye():
    bye_text = 'Okay, goodbye'
    return statement(bye_text)

if __name__ == '__main__':
    app.run(debug=True)