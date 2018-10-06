from twisted.internet import protocol
from helixir import IncompletePacket, decode_packet, encode_packet, _RPCRemote


class Protocol(protocol.Protocol):
    """
    Twisted protocol implementing the Perforce network protocol.

    ``packetReceived()`` is called when a perforce packet is received. Call
    ``sendPacket()`` to send a packet.
    """
    _buf = b""

    def dataReceived(self, data):
        self._buf += data
        while True:
            try:
                packet, self._buf = decode_packet(self._buf)
                self.packetReceived(packet)
            except IncompletePacket:
                break

    def packetReceived(self, packet):
        raise NotImplementedError

    def sendPacket(self, packet):
        self.transport.write(encode_packet(packet))


class RPCProtocol(Protocol):
    """
    Twisted protocol implementing the Perforce network protocol using an RPC
    pattern.

    Receiving a packet should be implemented by defining a method in a
    subclass. Call methods on ``self.remote`` to send a packet.
    """
    def __init__(self):
        self.remote = _RPCRemote(self.sendPacket)

    def packetReceived(self, packet):
        getattr(self, packet.func.replace("-", "__"))(
            *packet.args, **packet.kwargs)
