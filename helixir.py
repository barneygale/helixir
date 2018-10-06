import collections
import functools
import struct


# Packet header routines ------------------------------------------------------

class IncompletePacket(Exception):
    def __init__(self, minimum):
        self.minimum = minimum


def decode_packet_header(data):
    if len(data) < 5:
        raise IncompletePacket(5)

    header = struct.unpack('<BBBBB', data[:5])
    if header[0] != header[1] ^ header[2] ^ header[3] ^ header[4]:
        raise ValueError("Invalid checksum")

    length = struct.unpack('<xI', data[:5])[0] + 5
    if len(data) < length:
        raise IncompletePacket(length)

    return data[5:length], data[length:]


def encode_packet_header(data):
    header = list(struct.unpack('<BBBBB', struct.pack('<xI', len(data))))
    header[0] = header[1] ^ header[2] ^ header[3] ^ header[4]
    return struct.pack('<BBBBB', *header)


# Packet payload routines------------------------------------------------------

Packet = collections.namedtuple("Packet", ("func", "args", "kwargs"))


def decode_packet_payload(data):
    func = None
    args = []
    kwargs = {}

    while len(data) > 0:
        name,   data = data.split(b"\x00", 1)
        length, data = struct.unpack('<I', data[:4])[0], data[4:]
        value,  data = data[:length], data[length + 1:]
        if name == b"func":
            func = value
        elif name == b"":
            args.append(value)
        else:
            kwargs[name] = value

    return Packet(func, args, kwargs)


def encode_packet_payload(packet):
    payload = list(packet.kwargs.items())
    payload.extend((b"", arg) for arg in packet.args)
    payload.append((b"func", packet.func))

    data = b""
    for name, value in payload:
        data += name + b"\x00" + \
                struct.pack('<I', len(value)) + \
                value + b"\x00"
    return data


# Packet routines -------------------------------------------------------------

def decode_packet(data):
    """
    Decodes a packet from the beginning of the given byte string. Returns a
    2-tuple, where the first element is a ``Packet`` instance with "func",
    "args" and "kwargs" attributes, and the second element is a byte string
    containing any remaining data after the packet.
    """

    data, tail = decode_packet_header(data)
    packet = decode_packet_payload(data)
    return packet, tail


def encode_packet(packet):
    """
    Encodes a packet from the given ``Packet` instance. Returns a byte string.
    """

    data = encode_packet_payload(packet)
    data = encode_packet_header(data) + data
    return data


# Socket routines -------------------------------------------------------------

def receive_packet(sock):
    """
    Receive a perforce packet from the given socket. Returns a ``Packet``
    instance with "func", "args" and "kwargs" attributes.
    """
    data = b""
    while True:
        try:
            return decode_packet(data)[0]
        except IncompletePacket as exc:
            while len(data) < exc.minimum:
                data += sock.recv(exc.minimum - len(data))


def send_packet(sock, packet):
    """
    Send a perforce packet to the given socket.
    """
    sock.send(encode_packet(packet))


# Socket RPC classes ----------------------------------------------------------

class RPC(object):
    """
    Wrapper around a socket that provides an RPC interface to perforce. This
    class is intended to be subclassed.
    """
    running = False

    def __init__(self, sock):
        self.sock = sock
        self.remote = _RPCRemote(functools.partial(send_packet, self.sock))

    def run_once(self):
        packet = receive_packet(self.sock)
        getattr(self, packet.func.replace("-", "__"))(
            *packet.args, **packet.kwargs)

    def run_forever(self):
        self.running = True
        while self.running:
            self.run_once()


class _RPCRemote(object):
    def __init__(self, _send):
        self._send = _send

    def __getattr__(self, func):
        def fn(*args, **kwargs):
            self._send(Packet(func.replace("__", "-"), args, kwargs))
        return fn
