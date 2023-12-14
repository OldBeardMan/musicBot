def handle_response(message) -> str:
    p_message = message.lower()

    if "matt" in p_message:
        return 'If you want to know more about Matt check out: https://mattkrupa.net/'

    if "kuna" in p_message:
        return 'Kuna'

    if "sprytek" in p_message:
        return 'it is  me!'