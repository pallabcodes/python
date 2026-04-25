"""
Module: Low-Level Socket Selection (The asyncio Engine)
Target: L7 Performance Engineers (Core Python Standard)

Key Technique: selectors module
- High-level interface to epoll (Linux) and kqueue (BSD).
- Used to handle thousands of connections in a single thread.
- Zero-abstraction networking for maximum throughput.
"""

import selectors
import socket
import logging

logger = logging.getLogger(__name__)

def run_low_level_server(host='127.0.0.1', port=9999):
    """
    Implements a non-blocking server using epoll/kqueue.
    This is what 'asyncio' does under the hood.
    """
    sel = selectors.DefaultSelector()

    def accept(sock, mask):
        conn, addr = sock.accept()
        logger.info(f"Accepted connection from {addr}")
        conn.setblocking(False)
        # Register the new connection for READ events
        sel.register(conn, selectors.EVENT_READ, read)

    def read(conn, mask):
        try:
            data = conn.recv(1024)
            if data:
                logger.info(f"Received: {data.decode()} from {conn.getpeername()}")
                conn.send(data) # Echo
            else:
                logger.info(f"Closing connection {conn.getpeername()}")
                sel.unregister(conn)
                conn.close()
        except Exception as e:
            logger.error(f"Socket error: {e}")
            sel.unregister(conn)
            conn.close()

    # Setup the listening socket
    lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lsock.bind((host, port))
    lsock.listen()
    lsock.setblocking(False)
    
    # Register the listener for ACCEPT events
    sel.register(lsock, selectors.EVENT_READ, accept)

    logger.info(f"Low-level server listening on {host}:{port}...")
    try:
        while True:
            # The 'Wait' call - this is where the thread sleeps until IO happens
            events = sel.select(timeout=None)
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)
    except KeyboardInterrupt:
        logger.info("Server shutting down.")
    finally:
        sel.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Note: Run this and connect via 'telnet localhost 9999'
    # run_low_level_server()
