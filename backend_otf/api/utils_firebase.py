import firebase_admin
from firebase_admin import messaging


def send_message(token, title, text):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=text), token=token
    )
    try:
        response = messaging.send(message)
        print(f"Notificación enviada con éxito. ID de respuesta: {response}")
        return response
    except Exception as e:
        print(f"Error al enviar notificación de Firebase: {e}")
        return None


