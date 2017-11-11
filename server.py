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


LOCAL_IPS = map(str.strip, os.environ.get("LOCAL_IPS", "").split(","))
COUNTRIES_WITH_STATES = set(["US"])
@app.route("/")
def home():
    try:
        ip = flask.request.headers.getlist("X-Forwarded-For")[0]
    except Exception:
        ip =  flask.request.remote_addr

    country = "RO"
    region = ""
    try:
        if ip not in LOCAL_IPS:
            geo = GEO.city(ip)
            country = geo.country.iso_code
            if geo.country.iso_code in COUNTRIES_WITH_STATES:
                region = geo.subdivisions.most_specific.name
    except Exception:
        print("GeoIP failed for %s" % ip)

    now = time.time()
    events = []
    for event in DB.smembers("events"):
        if is_fresh("events:%s" % event, ref=now):
            data = json.loads(DB.get("events:%s:data" % event))
            if \
                    "place" in data and \
                    "location" in data["place"] and \
                    "cover" in data:
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
        country=country,
        region=region,
        maps_key=os.environ["MAPS_KEY"])
