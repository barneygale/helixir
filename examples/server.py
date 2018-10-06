from twisted.internet import reactor, protocol

from helixir_async import RPCProtocol


class RPC(RPCProtocol):
    def protocol(self, *args, **kwargs):
        print("PROTOCOL", args, kwargs)
        self.remote.protocol2("hello there", foo="456")

factory = protocol.Factory.forProtocol(RPC)
reactor.listenTCP(1667, factory)
reactor.run()
