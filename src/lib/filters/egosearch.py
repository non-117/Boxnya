# -*- coding: utf-8 -*-
import re

from lib.core import Filter

class EgoSearch(Filter):
    def init(self):
        try:
            self.regexp = self.regexp.decode("utf-8")
        except UnicodeDecodeError:
            self.regexp = ""
        self.pattern = re.compile(self.regexp)
        
        if isinstance(self.screen_name, str):
            self.screen_name = [self.screen_name]
        
        # オプション設定の読み込み
        self.favsync_sources = getattr(self, "favsync_sources", [])
        if isinstance(self.favsync_sources, str):
            self.favsync_sources = [self.favsync_sources]
        self.favtero = getattr(self, "favtero", False)
        self.filterRT = getattr(self, "filterRT", False)
    
    def isUnofficialRT(self, text):
        if not self.filterRT:
            return False
        regexp = r".*[RQ]T:?\s?@?[a-zA-Z0-9_].*"
        # searchがヒットしなければNoneが帰る
        result = re.search(regexp, text)
        return result
    
    def filter(self, packet):
        data = packet["data"]
        if not isinstance(data, dict):
            return None

        if data.get("mentions") and [user for user in self.screen_name if user in [mention["screen_name"] for mention in data["mentions"]]]:
            mention = {"user":data["user"]["screen_name"],
                       "post":data["text"]}
            if self.sendable(mention) and not self.isUnofficialRT(mention["post"]):
                self.send(u"%(user)s: %(post)s" % mention, exclude = ["favbot"])
                
                if self.favtero and "fav" in mention["post"] and mention["user"] in self.screen_name:
                    self.send({"text":mention["post"], "mention":data["mentions"], "type":"favtero"}, target=["favbot"])
        
        elif data.get("event") and data["target"]["screen_name"] in self.screen_name:
            if "favorite" in data["event"]:
                event = {"star":u"☆" if "un" in data["event"] else u"★",
                         "user":data["source"]["screen_name"],
                         "event":data["event"].title(),
                         "post":data["object"]["text"]}
                self.send(u"%(star)s %(user)s %(event)sd: %(post)s" % event, exclude = ["favbot"])
            
            elif "retweet" == data["event"]:
                event = {"user":data["source"]["screen_name"],
                         "post":data["object"]["text"]}
                self.send(u"%(user)s Retweeted: %(post)s" % event, exclude = ["favbot"])
            
            elif "dm" == data["event"]:
                event = {"user":data["source"]["screen_name"],
                         "post":data["text"]}
                self.send(u"DM from %(user)s: %(post)s" % event, exclude = ["favbot"])
            
            elif "follow" == data["event"]:
                event = {"name":data["source"]["name"],
                         "screen_name":data["source"]["screen_name"]}
                self.send(u"%(name)s (@%(screen_name)s) is now following you" % event, exclude = ["favbot"])
            
            elif "list" in data["event"]:
                event = {"event":u"◆ Added into" if "add" in data["event"] else u"◇ Removed from",
                         "list":data["object"]["name"]}
                self.send(u"%(event)s %(list)s" % event, exclude = ["favbot"])
        
        elif self.regexp and self.pattern.search(data.get("text", "")):
            mention = {"user":data["user"]["screen_name"],
                       "post":data["text"]}
            if self.sendable(mention):
                self.send(u"%(user)s: %(post)s" % mention, exclude = ["favbot"])
        
        elif data.get("event") == "favorite" and data["source"]["screen_name"] in self.favsync_sources:
            self.send({"id":data["object"]["id"],"type":"favsync"}, target = ["favbot"])