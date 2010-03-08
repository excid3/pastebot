#!/usr/bin/env python
"""
   PasteBot

   A minimal IRC bot for easy IRC pasting

   Written by Chris Oliver

   Includes python-irclib from http://python-irclib.sourceforge.net/

   This program is free software; you can redistribute it and/or
   modify it under the terms of the GNU General Public License
   as published by the Free Software Foundation; either version 2
   of the License, or any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program; if not, write to the Free Software
   Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA   02111-1307, USA.
"""


__author__ = "Chris Oliver <excid3@gmail.com>"
__version__ = "0.1.1"
__date__ = "11/27/2009"
__copyright__ = "Copyright (c) Chris Oliver"
__license__ = "GPL2"

import urllib
import urllib2
import irclib

# Send a notification
# If False, use a regular messsage
notify = True

class PasteBot:
    # Connection information
    network = 'irc.freenode.net'
    port = 6667
    network_pass = ''
    channels = ['#keryx']
    nick = 'Elmer'
    name = 'Elmer'
    nick_pass = ''

    pastes = {}

    def __init__(self):
            # Create an IRC object
        self.irc = irclib.IRC()

        # Setup the IRC functionality we want to log
        self.irc.add_global_handler('privmsg', self.handlePrivMessage)
        self.irc.add_global_handler('invite', self.handleInvite)
        
        # Create a server object, connect and join the channel
        self.server = self.irc.server()
        self.server.connect(self.network, self.port, 
                            self.nick, ircname=self.name, password=self.network_pass)
        self.server.privmsg("nickserv", "identify %s" % self.nick_pass)
        for channel in self.channels:
            self.server.join(channel)

        # Jump into an infinte loop
        self.irc.process_forever()

    def handleInvite(self, connection, event):
        """ User invites bot to join channel """
        connection.join(event.arguments()[0])    

        
    def handlePrivMessage(self, connection, event):
        text = event.arguments()[0]
        user = event.source()
        
        # Start a new paste
        if text.startswith("paste "):
            self.pastes[user] = {"channels": text.split()[1:],
                                      "text": ""}
        
        # Finish the paste and submit
        elif text == "end paste" and self.pastes.has_key(user):
            values = {'lang' : 'text',
                    'code' : self.pastes[user]["text"],
                    'parent' : '0'}
            params = urllib.urlencode(values)
            f = urllib2.urlopen('http://paste2.org/new-paste', params)
            data = f.read()
            url = f.geturl()
            f.close()
            
            print "Sending paste %s to %s" % (url, ", ".join(self.pastes[user]["channels"]))
             
            # Notify channels or people
            for channel in self.pastes[user]["channels"]:
                if channel.startswith("#"):
                    self.server.join(channel)
                
                # Send out the message
                msg = "%s would like you to view this paste: %s" % \
                      (user.split("!")[0], url)
                if notify:
                    self.server.notice(channel, msg)
                else:
                    self.server.privmsg(channel, msg)
                   
            # Message owner of success
            self.server.privmsg(user.split("!")[0], 
                                "Paste (%s) sent to: %s" % (url, 
                                ", ".join(self.pastes[user]["channels"])))
                   
            # Delete the paste
            del self.pastes[user]
           
        # We have a paste started so append text
        elif self.pastes.has_key(user):
            if self.pastes[user]["text"]:
                self.pastes[user]["text"] += "\n%s" % text
            else:
                self.pastes[user]["text"] = text
        else:
            # Ignore anything else and display help
            msg = ["To paste send me a PM in the following format:",
                  " ",
                  "paste <channels or usernames space separated>",
                  "<content to paste>",
                  "end paste",
                  " ",
                  "And there you have it, simple pasting straight to IRC",
                  "Be sure to check out http://excid3.com/projects for more apps."]
            for part in msg:
                self.server.privmsg(user.split("!")[0], part)
        

if __name__ == "__main__":
    bot = PasteBot()
