# adapters/telegram_conversation.py
import base64
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, filters, ApplicationBuilder, Application, ContextTypes

from telegram.error import InvalidToken

from .exceptions import TelegramInvalidTokenException, TelegramBotException, ErrorTelegram ,  bot_errors_handle

from anubis_core.ports.bots import IBotFlowPort, IConversationPort


class TelegramConversation(IConversationPort):
    def __init__(self, update, context: ContextTypes.DEFAULT_TYPE):
        self.update = update
        self.context = context
    @bot_errors_handle
    async def preguntar_texto(self, prompt, on_response):
        await self.update.message.reply_text(prompt)
        self.context.user_data["pending_callback"] = on_response
    @bot_errors_handle
    async def preguntar_opciones(self, prompt, opciones, on_response):
        botones = [InlineKeyboardButton(opt, callback_data=opt) for opt in opciones]
        markup = InlineKeyboardMarkup.from_column(botones)
        await self.update.message.reply_text(prompt, reply_markup=markup)
        self.context.user_data["pending_callback"] = on_response
    @bot_errors_handle
    async def preguntar_imagen(self, prompt, on_response):
        await self.update.message.reply_text(prompt)
        self.context.user_data["pending_callback"] = on_response
        self.context.user_data["esperando_imagen"] = True
    @bot_errors_handle
    async def mostrar_texto(self, texto):
        await self.update.message.reply_text(texto)
    
    async def mostrar_error(self, mensaje):
        await self.update.message.reply_text(f"❗<b>ERROR CRÍTICO</b>:\n {mensaje}\n Se ha cancelado el proceso",parse_mode="HTML" )        
    
    @bot_errors_handle
    async def mostrar_resumen(self, titulo, datos: dict):
        resumen = "\n".join([f"{k}: {v}" for k, v in datos.items()])
        await self.update.message.reply_text(f"{titulo}:\n\n{resumen}")

    @bot_errors_handle
    async def obtener_imagen(self, image_id: str) -> str:
        """Descarga una imagen desde Telegram y la convierte a base64"""
        try:
            archivo = await self.context.bot.get_file(image_id)
            imagen_bytes = await archivo.download_as_bytearray()
            return base64.b64encode(imagen_bytes).decode("utf-8")
        except:
            raise TelegramBotException(ErrorTelegram.IMAGEN_ESPERADA_NO_VALIDA,None)
        
    @bot_errors_handle
    async def obtener_imagen(self, image: bytes) -> str:
        try:
            return base64.b64encode(image).decode('utf-8')
        except:
            raise TelegramBotException(ErrorTelegram.IMAGEN_ESPERADA_NO_VALIDA,None)

class TelegramBotCommand():
    def __init__(self, telegram_api_token, id_auths, flow: IBotFlowPort):
        
        self.token = telegram_api_token
        self.id_auths = id_auths
        self.flow = flow
        self.application: Application = None
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler("start", self._start))
        self.application.add_handler(CommandHandler("help", self._help))
        self.application.add_handler(CommandHandler("cancel", self._cancel))
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
    @bot_errors_handle
    def bind(self):
        try:
            self.application.run_polling()
        except InvalidToken as e:
            raise TelegramInvalidTokenException("Token no valido")
    
    async def _start(self, update, context):
        conv = TelegramConversation(update, context)
        context.user_data["flow"] = self.flow
        await self.flow.start(conv, context.user_data)
    
    async def _help(self, update, context):
        conv = TelegramConversation(update, context)
        context.user_data["flow"] = self.flow
        await self.flow.help(conv, context.user_data)      
    
    async def _cancel(self, update, context):
        context.user_data.clear()
        await update.message.reply_text("Operación cancelada.")  
    
    async def handle_message(self, update, context):
        if "pending_callback" in context.user_data:
            cb = context.user_data.pop("pending_callback")
            context.user_data.pop("esperando_imagen", None)
            await cb(update.message.text)
    
    async def handle_callback(self, update, context):
        if "pending_callback" in context.user_data:
            cb = context.user_data.pop("pending_callback")
            await cb(update.callback_query.data)
    
    async def handle_photo(self, update, context):
        if context.user_data.get("esperando_imagen"):
            cb = context.user_data.pop("pending_callback")
            context.user_data.pop("esperando_imagen")
            file = await update.message.photo[-1].get_file()
            img_bytes = await file.download_as_bytearray()
            await cb(img_bytes)
