# coding=utf-8
import dateutil.parser
import dotenv
import flask
import geoip2.database
import json
import os
import redis
import time
import urllib


dotenv.load_dotenv(dotenv.find_dotenv())


app = flask.Flask(__name__)
DB = redis.StrictRedis()
GEO = geoip2.database.Reader(os.path.join(app.root_path, "GeoLite2-City.mmdb"))

app.jinja_env.filters["strftime"] = \
    lambda str, fmt: dateutil.parser.parse(str).strftime(fmt)
app.jinja_env.filters["quote_plus"] = lambda u: urllib.quote_plus(u)


STATIC = os.path.join(app.root_path, "static")
@app.route("/favicon.ico")
def favicon():
    return flask.send_from_directory(
        STATIC,
        "favicon.ico",
        mimetype="image/png")


STALE_AFTER = 30 * 60
def is_fresh(key, ref=None):
    now = ref or time.time()
    mtime = DB.get("%s:updated" % key) or "0"
    return now - float(mtime) <= STALE_AFTER



WITH_STATES = set(["US"])
@app.route("/")
def home():
    try:
        ip = flask.request.headers.getlist("X-Forwarded-For")[0]
    except Exception:
        ip =  flask.request.remote_addr
    try:
        geo = GEO.city(ip)
    except Exception:
        geo = GEO.city("5.2.128.0")

    now = time.time()
    events = []
    for event in DB.smembers("events"):
        if is_fresh("events:%s" % event, ref=now):
            data = json.loads(DB.get("events:%s:data" % event))
            if "place" in data and "location" in data["place"]:
                events.append({
                    "id": data["id"],
                    "lat": data["place"]["location"]["latitude"],
                    "lng": data["place"]["location"]["longitude"],
                    "attending_count": data["attending_count"],
                    "interested_count": data["interested_count"],
                    "html": flask.render_template("event.html", event=data) 
                })

    return flask.render_template("homepage.html",
        events=events,
        country=geo.country.iso_code,
        region=geo.subdivisions.most_specific.name if geo.country.iso_code in WITH_STATES else "",
        maps_key=os.environ["MAPS_KEY"])
