"""UDP proxy server."""

import itertools
import asyncio
import asgiref.sync
import time
import numpy as np
import matplotlib.pyplot as plt
import os
from threading import Thread

readings = []

server_pool = {('127.0.0.1',55):0,('127.0.0.1',56):0,('127.0.0.1',57):0}
server_cycle = itertools.cycle(server_pool)

class ProxyDatagramProtocol(asyncio.DatagramProtocol):

    def __init__(self, remote_address):
        self.remote_address = remote_address
        self.remotes = {}
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport
        #print("sending to addr:",self.transport)

    async def _do_data(self, data, addr):
        if addr in self.remotes:
            #print("Message from addr:", addr)
            
            if self.remotes[addr].transport is None:
                try:
                    await asyncio.wait_for(self.remotes[addr].transport_event.wait(), timeout=2)
                except:
                    print("RemoteDatagramProtocol connection timeout...")
                    return 

            self.remotes[addr].transport.sendto(data)
            return

        loop = asyncio.get_event_loop()
        
        try:
            server = await asyncio.wait_for(get_server(), timeout=10)
            assert server is not None, "no server"
        except:
            return 

        self.remotes[addr] = RemoteDatagramProtocol(self, addr, data)

        coro = loop.create_datagram_endpoint(
            lambda: self.remotes[addr], remote_addr=server)

        await coro

    def datagram_received(self, data, addr):
        asyncio.ensure_future(self._do_data(data, addr))
        


class RemoteDatagramProtocol(asyncio.DatagramProtocol):

    def __init__(self, proxy, addr, data):
        self.proxy = proxy
        self.addr = addr
        self.data = data
        self.transport = None
        self.transport_event = asyncio.Event()
        super().__init__()

    def connection_made(self, transport):
        # transport = server, addr = client
        print("Connection made to:", self.addr)
        self.transport_event.set()
        self.transport = transport

        self.transport.sendto(self.data)

    def datagram_received(self, data, _):
        self.proxy.transport.sendto(data, self.addr)
        server_pool[self.transport._address] = max(server_pool[self.transport._address]-1, 0)
        print(server_pool)

    def connection_lost(self, exc):
        print("Connection lost...")
        self.proxy.remotes.pop(self.attr)


async def start_datagram_proxy(bind, port):
    loop = asyncio.get_event_loop()

    protocol = ProxyDatagramProtocol((1,1))
    return await loop.create_datagram_endpoint(
        lambda: protocol, local_addr=(bind, port))



async def get_server():
    num = len(server_pool)
    while num > 0:
        server = next(server_cycle)
        if server_pool[server] < 2:
            server_pool[server] += 1
            readings.append(time.time())
            return server

        num -= 1


def main(bind='127.0.0.1', port=53,):
    loop = asyncio.get_event_loop()
    print("Starting datagram proxy...")
    coro = start_datagram_proxy(bind, port)
    transport, _ = loop.run_until_complete(coro)
    print("Datagram proxy is running...")
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    print("Closing transport...")
    transport.close()
    loop.close()


def draw_graph():
    x = np.array([i for i in readings if i!=None])
    y = np.array([i for i in range(len(x))])
    plt.ylabel("Time")
    plt.xlabel("Request Count")
    
    for i in range(len(x)):
        plt.scatter(y[i],x[i])
        plt.pause(0.000001)
    
    plt.show()


if __name__ == '__main__':
    main()
    draw_graph()

