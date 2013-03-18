#! /usr/bin/env python
#
# Example program using irc.bot.
#
# Joel Rosdahl <joel@rosdahl.net>

"""A simple example bot.

This is an example bot that uses the SingleServerIRCBot class from
irc.bot.  The bot enters a channel and listens for commands in
private messages and channel traffic.  Commands in channel messages
are given by prefixing the text by the bot name followed by a colon.
It also responds to DCC CHAT invitations and echos data sent in such
sessions.

The known commands are:

    stats -- Prints some channel information.

    disconnect -- Disconnect the bot.  The bot will try to reconnect
                  after 60 seconds.

    die -- Let the bot cease to exist.

    dcc -- Let the bot invite you to a DCC CHAT connection.
"""

import irc.bot
import irc.strings
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
import time

class Quote(object):
    def __init__(self, search, quote, delay=60):
        self.search = search
        self.quote = quote
        self.time = 0
        self.delay = delay

    def enough_time_passed(self):
        return time.time() - self.time > self.delay

    def update_time(self):
        self.time = time.time()

class TestBot(irc.bot.SingleServerIRCBot):
    quotes = []

    def __init__(self, channel, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.channel = channel

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        c.join(self.channel)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0])

    def on_pubmsg(self, c, e):
        user = e.source
        channel = e.target
        message = e.arguments[0] # always a list with one element

        for q in self.quotes:
            if q.search in message:
                if q.enough_time_passed():
                    c.privmsg(channel, q.quote)
                    q.update_time()
                else:
                    print "Quote matched, but not enough time elapsed!"

    def on_dccmsg(self, c, e):
        c.privmsg("You said: " + e.arguments[0])

    def on_dccchat(self, c, e):
        if len(e.arguments) != 2:
            return
        args = e.arguments[1].split()
        if len(args) == 4:
            try:
                address = ip_numstr_to_quad(args[2])
                port = int(args[3])
            except ValueError:
                return
            self.dcc_connect(address, port)

    def do_command(self, e, cmd):
        nick = e.source.nick
        c = self.connection

        if cmd == "disconnect":
            self.disconnect()
        elif cmd == "die":
            self.die()
        elif cmd == "stats":
            for chname, chobj in self.channels.items():
                c.notice(nick, "--- Channel statistics ---")
                c.notice(nick, "Channel: " + chname)
                users = chobj.users()
                users.sort()
                c.notice(nick, "Users: " + ", ".join(users))
                opers = chobj.opers()
                opers.sort()
                c.notice(nick, "Opers: " + ", ".join(opers))
                voiced = chobj.voiced()
                voiced.sort()
                c.notice(nick, "Voiced: " + ", ".join(voiced))
        # elif cmd == "dcc":
        #     dcc = self.dcc_listen()
        #     c.ctcp("DCC", nick, "CHAT chat %s %d" % (
        #         ip_quad_to_numstr(dcc.localaddress),
        #         dcc.localport))
        else:
            c.notice(nick, "Not understood: " + cmd)

def main():
    # TODO: read this stuff from a config file?
    server = "irc.freenode.net"
    port = 6667

    channel = "#SpaceGoatsChat"
    nickname = "SpaceGoatsBot"

    bot = TestBot(channel, nickname, server, port)

    # TODO: load quotes from a file, or something
    bot.quotes = [
        Quote("test", "test passed"),
        Quote("lunch", "http://www.youtube.com/watch?v=XU1wk2HWtwA"),
        Quote("the mall", "http://www.youtube.com/watch?v=IY_bhVSGKEg"),

        Quote("...", "...", delay=(60*5)),
        Quote(">.>", "<.<", delay=(60*5)),
        Quote("<.<", ">.>", delay=(60*5)),

    ]

    bot.start()

if __name__ == "__main__":
    main()
