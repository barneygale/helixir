from twisted.internet import protocol, reactor

from helixir_async import Protocol


HOST = "127.0.0.1"
PORT = 1668


class ClientProtocol(Protocol):
    clientFactory = None

    def __init__(self, clientFactory):
        self.clientFactory = clientFactory

    def connectionMade(self):
        # Flush queue
        self.clientFactory.passUp(None)

    def connectionLost(self, reason=None):
        self.clientFactory.closeDown()

    def packetReceived(self, packet):
        self.clientFactory.passDown(packet)


class ClientFactory(protocol.ClientFactory):
    protocol = ClientProtocol

    serverProtocol = None
    clientProtocol = None

    def __init__(self, serverProtocol):
        self.serverProtocol = serverProtocol
        self.queued = []

    def buildProtocol(self, addr):
        self.clientProtocol = ClientProtocol(self)
        return self.clientProtocol

    def passUp(self, packet):
        if packet:
            self.queued.append(packet)
        if self.clientProtocol and self.clientProtocol.connected:
            for packet in self.queued:
                self.log("up", packet)
                self.clientProtocol.sendPacket(packet)
            del self.queued[:]

    def passDown(self, packet):
        self.log("down", packet)
        self.serverProtocol.sendPacket(packet)

    def closeDown(self):
        self.serverProtocol.transport.loseConnection()

    def log(self, direction, packet):
        print("%s %s%s" % (
            ">>>" if direction == "up" else "<<<",
            packet.func,
            tuple(packet.args)))
        for key, value in sorted(packet.kwargs.items()):
            print("        %-15s %s" % (key, value))


class ServerProtocol(Protocol):
    clientFactory = None

    def connectionMade(self):
        print("-" * 79)
        self.clientFactory = ClientFactory(self)
        reactor.connectTCP(HOST, PORT, self.clientFactory)

    def connectionLost(self, reason=None):
        print("+" * 79)

    def packetReceived(self, packet):
        self.clientFactory.passUp(packet)


class ServerFactory(protocol.Factory):
    protocol = ServerProtocol


def main():
    serverFactory = ServerFactory()
    reactor.listenTCP(1667, serverFactory)
    reactor.run()

if __name__ == '__main__':
    main()
