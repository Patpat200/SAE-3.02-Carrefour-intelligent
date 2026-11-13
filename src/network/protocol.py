import json


MAX_MESSAGE_BYTES = 1024 * 1024


def encode_message(payload):
    texte = json.dumps(payload, ensure_ascii=False) + "\n"
    return texte.encode("utf-8")


def decode_messages(buffer):
    messages = []
    # TCP peut couper un message. On garde le reste pour la prochaine lecture.
    while b"\n" in buffer:
        morceaux = buffer.split(b"\n", 1)
        raw_message = morceaux[0]
        buffer = morceaux[1]
        if len(raw_message) > MAX_MESSAGE_BYTES:
            raise ValueError("Message trop long")
        if raw_message.strip() == b"":
            continue
        message = json.loads(raw_message.decode("utf-8"))
        messages.append(message)
    if len(buffer) > MAX_MESSAGE_BYTES:
        raise ValueError("Message trop long")
    return messages, buffer
