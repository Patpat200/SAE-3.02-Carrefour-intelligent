import json


def encode_message(payload):
    texte = json.dumps(payload, ensure_ascii=False) + "\n"
    return texte.encode("utf-8")


def decode_messages(buffer):
    messages = []
    while b"\n" in buffer:
        morceaux = buffer.split(b"\n", 1)
        raw_message = morceaux[0]
        buffer = morceaux[1]
        if raw_message.strip() == b"":
            continue
        message = json.loads(raw_message.decode("utf-8"))
        messages.append(message)
    return messages, buffer
