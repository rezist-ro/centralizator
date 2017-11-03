# coding=utf-8
import redis

DB = redis.StrictRedis()

for event in DB.smembers("events"):
    DB.delete("events:%s:updated" % event)
    