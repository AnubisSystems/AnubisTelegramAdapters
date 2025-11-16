import functools
import inspect
import logging
from anubis_core.common.exceptions import AnubisException, AnubisDomainException, AnubisBaseAplicationException, AnubisBaseAdapterException, EnumExceptionsTemplate

class ErrorTelegram(EnumExceptionsTemplate):
    IMAGEN_ESPERADA_NO_VALIDA = ("imagen_valida", "No se a recibido una imagen valida")


class TelegramBotException(AnubisBaseAdapterException):
    def __init__(self, codigo_error, contexto=None, original=None):
        super().__init__(TelegramBotException, codigo_error, contexto, original)    

class TelegramInvalidTokenException(Exception):
    pass

logger = logging.getLogger("entrada")

def bot_errors_handle(func):
    if inspect.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            he_self = args[0] if args else None
            bot_conv = he_self if type(he_self).__name__ == "TelegramConversation" else he_self.flow.conv

            try:
                return await func(*args, **kwargs)
            except TelegramInvalidTokenException as e:
                raise e
            except TelegramBotException as e:
                logger.error(f"[TelegramBotException] {str(e)}", exc_info=True)
                if hasattr(bot_conv, "mostrar_error"):
                    mensaje = str(e)
                    await bot_conv.mostrar_error(f"telegram: {mensaje}")
                return {"error": "Error en adaptador telegram", "detalle": str(e)}
            except AnubisException as e:
                tipo = e.tipo_excepcion.__name__
                codigo = e.codigo_error.codigo
                mensaje = str(e)

                logger.error(f"[{tipo}] {codigo} - {mensaje}", exc_info=True)

                if hasattr(bot_conv, "mostrar_error"):
                    await bot_conv.mostrar_error(mensaje)

                if e.tipo_excepcion is AnubisDomainException:
                    return {"error": "Error de negocio", "detalle": mensaje}
                elif e.tipo_excepcion is AnubisBaseAdapterException:
                    return {"error": "Error técnico", "detalle": mensaje}
                elif e.tipo_excepcion is AnubisBaseAplicationException:
                    return {"error": "Error interno", "detalle": mensaje}
                else:
                    return {"error": "Error desconocido", "detalle": mensaje}
            except Exception as e:
                logger.exception("Excepción no controlada")
                if hasattr(bot_conv, "mostrar_error"):
                    await bot_conv.mostrar_error("❌ Error inesperado en el sistema.")
                return {"error": "Error inesperado", "detalle": str(e)}
        return async_wrapper

    else:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            he_self = args[0] if args else None  # Captura el objeto (self) si existe

            if type(he_self).__name__ == "TelegramConversation":
                bot_conv= he_self
            else:
                bot_conv = he_self.flow.conv

            try:
                return func(*args, **kwargs)
            except TelegramBotException as e:
                pass
            except TelegramInvalidTokenException as e:
                raise e
            except AnubisException as e:
                tipo = e.tipo_excepcion.__name__
                codigo = e.codigo_error.codigo
                mensaje = str(e)

                logger.error(f"[{tipo}] {codigo} - {mensaje}", exc_info=True)

                # Aquí decides cómo responder según la capa
                if e.tipo_excepcion is AnubisDomainException:
                    return {"error": "Error de negocio", "detalle": mensaje}
                elif e.tipo_excepcion is AnubisBaseAdapterException:
                    bot_conv.mostrar_error(mensaje)
                    return {"error": "Error interno", "detalle": mensaje}
                    
                elif e.tipo_excepcion is AnubisBaseAplicationException:
                    return {"error": "Error técnico", "detalle": mensaje}
                elif e.tipo_excepcion is TelegramBotException:
                    return {"error": "Error en adaptador telegram", "detalle": mensaje}
                else:
                    return {"error": "Error desconocido", "detalle": mensaje}

            except Exception as e:
                logger.exception("Excepción no controlada")
                return {"error": "Error inesperado", "detalle": str(e)}
        return sync_wrapper

