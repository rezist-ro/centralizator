# coding=utf-8
import facebook
import json
import os
import redis
import requests
import time

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


def update_events():
    now = time.time()
    for event in DB.smembers("events"):
        if is_stale("events:%s" % event, ref=now):
            print("Updating %s" % event)
            try:
                data = FB.get_object(id=event, fields=FIELDS)
                if \
                        "place" in data and \
                        "name" in data["place"] and \
                        "location" not in data["place"]:
                    try:
                        response = requests.get(GEOCODE_URL, params={
                            "address": data["place"]["name"],
                            "key": os.environ["GEOCODE_KEY"]
                        })
                        geometry = response.json()["results"][0]["geometry"]
                        data["place"]["location"] = {
                            "latitude": geometry["location"]["lat"],
                            "longitude": geometry["location"]["lng"]
                        }
                        print("Location patched")
                    except Exception as e:
                        print("Geocode failed")
                DB.set("events:%s:data" % event, json.dumps(data))
                DB.set("events:%s:updated" % event, now)
                print("OK")
                time.sleep(1.0)
            except Exception as e:
                print("Failed", e)
                time.sleep(60.0)


while True:
    update_events()
    time.sleep(10.0)
