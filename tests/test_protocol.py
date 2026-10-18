import json
import socket
import unittest
from bloomjoin.protocol import Channel


class ProtocolTests(unittest.TestCase):
    def test_round_trip_and_exact_byte_accounting(self):
        left, right = socket.socketpair()
        with left, right:
            sender, receiver = Channel(left), Channel(right)
            message = {"rows": [[7, "payload"]]}
            sender.send(message)
            self.assertEqual(receiver.receive(), message)
            expected = 4 + len(json.dumps(message, separators=(",", ":")).encode("utf-8"))
            self.assertEqual(sender.bytes_sent, expected)
            self.assertEqual(receiver.bytes_received, expected)

    def test_truncated_message_raises(self):
        left, right = socket.socketpair()
        with left, right:
            left.sendall(b"\x00\x00")
            left.shutdown(socket.SHUT_WR)
            with self.assertRaises(ConnectionError):
                Channel(right).receive()
