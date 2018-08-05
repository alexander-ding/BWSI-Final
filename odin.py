import pooja as pj
import thorben as tb
import pinar as pn
import genre_recognition as gr
import emotions
import random
import webbrowser
import urllib.parse as parse

from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
from pathlib import Path

print("Loading pooja")
pj_db = pj.database()
pj_db.load("data/song_db.dat")
print("pooja loaded")

print("Loading thorben")
tb_db = tb.Database()
tb_db.load("data/face_db.dat")
print("thorben loaded")

print("Loading pinar")
pn_db = pn.Database()
pn_db.load("data/img_db.dat")
print("pinar loaded")

app = Flask(__name__)
ask = Ask(app, '/')

ps = []

@app.route('/')
def homepage():
    return "Hello"

@ask.launch
def start_skill():
    welcome_messages = ["Welcome! What would you like me to do?"]
    n = random.randint(0,len(welcome_messages)-1)
    
    return question(welcome_messages[n]).reprompt("Sorry, I didn't catch that, perhaps ask me to talk about my skills")

@ask.intent("AMAZON.HelpIntent")
def help():
    long_helpful_text = "I can read your face! If you're not in the database, tell me to learn your face. I can also identify the music you're playing and guess it's genre. Also, tell me to look up images of interesting things"
    return statement(long_helpful_text)

@ask.intent("SongIntent")
def matching_song():
    audio = pj.input_mic(5)
    result = pj_db.match_song(audio)
    if result is None:
        session.attributes["song_retry"] = True
        return question("Sorry, I can't match this song. Would you like me to try again?")
    return statement(result)

@ask.intent("GenreIntent")
def match_genre():
    audio = pj.input_mic(5) / 2**16
    result = gr.get_label(audio)
    return statement("I think this is {} music".format(result))

@ask.intent("GoodBoiIntent")
def thanks():
    outs = ["Love you!",
            "Aw, you're welcome",
            "At your service"]
    id = random.randint(0,len(outs)-1)
    return statement(outs[id])

@ask.intent("AMAZON.YesIntent")
def yes_intent():
    # parse different cases
    if session.attributes.get("song_retry") is not None:
        session.attributes["song_retry"] = None
        return matching_song()
    elif session.attributes.get("get_name") is not None:
        session.attributes["get_name"] = None
        return add_face_confirmed()
    
    return fallback()

@ask.intent("AMAZON.NoIntent")
def no_intent():
    if session.attributes.get("song_retry") is not None:
        session.attributes["song_retry"] = None
        return statement("Okay")
    elif session.attributes.get("get_name") is not None:
        session.attributes["get_name"] = None
        global ps
        ps = []
        return statement("Okay. No new face is learned")

@ask.intent("FaceAddIntent")
def adding_face():
    global ps
    for i in range(1,5):
        ps.append(tb.from_camera())
    if len(ps) == 0:
        return statement("Sorry. I can't identify your face. Make sure that only one person is in front of the camera and that your whole face is there.")
    session.attributes["get_name"] = True
    return question("Okay, I got your pictures. What is your name?")

def add_face_confirmed():
    name = session.attributes["name"]
    id = tb_db.add_user(name)
    global ps
    for p in ps:
        tb_db.add_image(p, id)
    ps = []
    tb_db.store("data/face_db.dat")
    return statement("You're all set, {}!".format(name))

@ask.intent("NameIntent", mapping={"first":"first_name","last":"last_name"}) 
def get_name(first, last):
    if session.attributes.get("get_name") is None:
        return fallback()
    session.attributes["name"] = "{} {}".format(first,last)
    return question("Your name is {} {}, right?".format(first,last))

@ask.intent("FaceRecIntent")
def recognizing_face():
    picture = tb.from_camera()
    labels = emotions.emotion(picture)
    ret_data = tb_db.match(picture)
    if len(ret_data) == 0:
        return statement("I don't see any faces")
    
    names = []
    unseen_cnt = 0
    for _,_,label in ret_data:
        if label is None:
            unseen_cnt += 1
        else:
            names.append(label)
    if unseen_cnt > 0:
        names.append("{} unrecognized face".format(unseen_cnt))
    elif unseen_cnt > 1:
        names.append("{} unrecognized faces".format(unseen_cnt))
    out = "I see "
    if len(names) == 1:
        out = out + names[0] + ". "
    else:
        out = out + ", ".join(names[:-1]) + ", and " + names[-1] + ". "
    if len(labels) == 1:
        out += "You seem {} or {}.".format(labels[0][0], labels[0][1])
    else:
        for l in labels:
            out += "One of you seem {} and {}. ".format(l[0], l[1]) 
    return statement(out)

@ask.intent("ImageIntent", mapping={"query":"ImageQuery"})
def keyword_images(query):
    webbrowser.open_new("http://localhost:5001/search_by_text?" + parse.urlencode({'query':query}))
    return statement("Here you go. The results are on the computer.")

@ask.intent("AMAZON.FallbackIntent")
def fallback():
    out = ["Sorry, I don't think I can help with that. Ask me to talk about my skills if you want to learn more.",
    "Sorry, I can't help with that."]
    id = random.randint(0,len(out)-1)
    return question(out[id])
@ask.intent("AMAZON.StopIntent")
@ask.intent("AMAZON.CancelIntent")
def bye():
    bye_text = 'Okay, goodbye'
    return statement(bye_text)

app.run(debug=True,port=5000)