import unittest

from src.network.protocol import decode_messages, encode_message


class ProtocolTests(unittest.TestCase):
    def test_fragmented_json_and_unicode(self):
        message = {"type": "error", "message": "Priorité refusée"}
        data = encode_message(message)
        cut = data.index("é".encode("utf-8")) + 1
        messages, rest = decode_messages(data[:cut])
        self.assertEqual(messages, [])
        messages, rest = decode_messages(rest + data[cut:])
        self.assertEqual(messages, [message])
        self.assertEqual(rest, b"")

    def test_multiple_messages_and_partial_tail(self):
        data = b'\n{"type":"state","payload":{}}\n{"type":"error","message":"Non"}\n{"type":'
        messages, rest = decode_messages(data)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], {"type": "state", "payload": {}})
        self.assertEqual(rest, b'{"type":')

    def test_invalid_json_is_reported(self):
        with self.assertRaises(ValueError):
            decode_messages(b'{invalide}\n')


if __name__ == "__main__":
    unittest.main()
