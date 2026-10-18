"""Length-prefixed UTF-8 JSON; counters include the four-byte prefix.

Each endpoint counts its own sends/receives. Report one endpoint's sum to
avoid counting the same wire bytes twice. TCP/IP headers are excluded.
"""
import json
import struct


class Channel:
    def __init__(self, connection):
        self.connection = connection
        self.bytes_sent = 0
        self.bytes_received = 0

    def send(self, message):
        body = json.dumps(message, separators=(",", ":")).encode("utf-8")
        packet = struct.pack("!I", len(body)) + body
        self.connection.sendall(packet)
        self.bytes_sent += len(packet)

    def _read(self, size):
        data = bytearray()
        while len(data) < size:
            chunk = self.connection.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Peer closed before the message was complete")
            data.extend(chunk)
        self.bytes_received += size
        return bytes(data)

    def receive(self):
        size = struct.unpack("!I", self._read(4))[0]
        return json.loads(self._read(size).decode("utf-8"))
