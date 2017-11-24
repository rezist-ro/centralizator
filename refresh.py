# coding=utf-8
import dotenv
import facebook
import hashlib
import json
import os
import redis
import requests
import time


dotenv.load_dotenv(dotenv.find_dotenv())


GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
FB = facebook.GraphAPI(
    access_token=os.environ["FACEBOOK_KEY"],
    version=2.10
)
DB = redis.StrictRedis()
FIELDS = "name,description,cover,place,start_time,end_time,event_times," + \
         "attending_count,interested_count,maybe_count,declined_count"


STALE_AFTER = 15 * 60
def is_stale(key, ref=None):
    now = ref or time.time()
    mtime = DB.get("%s:updated" % key) or "0"
    return now - float(mtime) > STALE_AFTER


def geocode(location):
    key = hashlib.sha1(location.encode("utf-8")).hexdigest()
    cached = DB.get("geocache:%s:data" % key)
    if cached:
        cached = json.loads(cached)
    else:
        print("Looking up %s" % location.encode("utf-8"))
        response = requests.get(GEOCODE_URL, params={
            "address": location,
            "key": os.environ["GEOCODE_KEY"]
        })
        geometry = response.json()["results"][0]["geometry"]
        cached = (geometry["location"]["lat"], geometry["location"]["lng"])
        DB.set("geocache:%s:data" % key, json.dumps(cached))
    return cached


def update_events():
    now = time.time()
    for event in DB.smembers("events"):
        if is_stale("events:%s" % event, ref=now):
            print("Updating %s" % event)
            try:
                data = FB.get_object(id=event, fields=FIELDS)
                override = DB.get("events:%s:override" % event)
                if override:
                    override = override.decode("utf-8")
                if override or (
                        "place" in data and \
                        "name" in data["place"] and \
                        "location" not in data["place"]):
                    try:
                        lat, lng = geocode(override or data["place"]["name"])
                        data["place"]["location"] = {
                            "latitude": lat,
                            "longitude": lng
                        }
                    except Exception as e:
                        print("Geocode failed", e)
                DB.set("events:%s:data" % event, json.dumps(data))
                DB.set("events:%s:updated" % event, now)
                print("OK")
            except Exception as e:
                print("Failed", e)
            finally:
                time.sleep(1.0)


while True:
    update_events()
    time.sleep(60.0)
