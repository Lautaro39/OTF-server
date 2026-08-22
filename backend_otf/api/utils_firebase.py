from firebase_admin import messaging
from .models import Notificacion


def notify_user(denuncia, title, body):
    try:
        usuario = denuncia.id_usuario

        notification = Notificacion.objects.create(
            id_usuario=denuncia.id_usuario,
            tipo="Denuncia",
            contenido=body,
        )

        if hasattr(usuario, "infousuario"):  # Verifica si el usuario tiene InfoUsuario
            tokenFcm = usuario.infousuario.token_fcm
            if tokenFcm:  # Verifica si tiene un token guardado
                send_message(token=tokenFcm, title=title, body=body)

    except Exception as e:
        # Si falla la red de Firebase, mostramos el error en consola pero NO detenemos la API
        print(f"[ERROR] No se pudo enviar la notificación push: {e}")


def send_message(token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body), token=token
    )
    try:
        response = messaging.send(message)
        print(f"Notificación enviada con éxito. ID de respuesta: {response}")
        return response
    except Exception as e:
        print(f"Error al enviar notificación de Firebase: {e}")
        return None
