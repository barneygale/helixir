Helixir: Python interface to Perforce RPC
=========================================

This Python library lets you interact with the Perforce remote procedure call
(RPC) API, which is the lowest-level API used by the Perforce network protocol.
This interface is undocumented and quite ancient, so you'll need to spin up a
proxy (see 'examples/proxy.py') to check what the official client and server
send. This library implements the API natively and does not require official
Perforce binaries.


Installation
------------

To install::

    $ pip install git+https://github.com/barneygale/helixir.git


Usage
-----


Working with byte strings
~~~~~~~~~~~~~~~~~~~~~~~~~

If you're dealing with perforce packets in byte string form, use the
``helixir.encode_packet()`` and ``helixir.decode_packet()`` functions. These
work with ``helixir.Packet`` objects, which are namedtuples with 'func', 'args'
and 'kwargs' attributes.


Working with sockets
~~~~~~~~~~~~~~~~~~~~

If you're working with a socket object, use the ``helixir.receive_packet()``
and ``helixir.send_packet()`` functions. These return/accept ``Packet``
objects.

You can also wrap a socket in an RPC interface. To do this, subclass
``helixir.RPC`` and implement methods for any packets you'll handle.
Instantiate your subclass passing it a connected socket object. You can send
packets by calling ``self.remote.funcNameHere()`` from a packet handler. You'll
need to call ``run_once()`` or ``run_forever()`` to receive and dispatch
packets. For example::

    import socket
    import helixir

    class MyRPC(helixir.RPC):
        def goodbye(name=None):
            print("got goodbye packet")
            #self.remote.blargh("foo", bar="yes")

    sock = socket.create_connection(("127.0.0.1", 1666))
    rpc = MyRPC(sock)
    rpc.remote.hello(name="bob")  # Send a "hello" packet
    rpc.run_once()                # Receive a "goodbye" packet
    sock.close()


Working with Twisted
~~~~~~~~~~~~~~~~~~~~

When writing a server you may want to use an asynchronous framework. Helixir
provides support for this in the ``helixir_async`` module, which requires
twisted.

The ``helixir_async.Protocol`` class is a twisted protocol implementing
the perforce network protocol. Call ``sendPacket()`` to send a packet. The
``packetReceived()`` method is called on receipt of a packet.

The ``helixir_async.RPCProtocol`` class is a subclass that dispatches received
packets to instance methods, much like the ``helixir.RPC`` class described
above. As before, ``self.remote.doSomething()`` can be used to call a method on
the remote (i.e. send a packet).

To implement a client::

    from twisted.internet import protocol, reactor
    from helixir_async import RPCProtocol

    class MyRPCClient(RPCProtocol):
        def connectionMade():
            self.remote.hello(name='fred')

        def goodbye(name=None):
            pass

    factory = protocol.ClientFactory.forProtocol(MyRPCClient)
    reactor.connectTCP('127.0.0.1', 1666, factory)
    reactor.run()

To implement a server::

    from twisted.internet import protocol, reactor
    from helixir_async import RPCProtocol

    class MyRPCServer(RPCProtocol):
        def hello(name):
            self.remote.goodbye(name=name)

    factory = protocol.Factory.forProtocol(MyRPCServer)
    reactor.listenTCP(1666, factory)
    reactor.run()

