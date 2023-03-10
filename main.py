from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, ParseMode
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
from os import getenv
import psycopg2
import json
import requests
import re
import weather


location, latitud, longitud = '', [], []


def consultbd(chat_id): # Consultas generales a la base de datos
    conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
    cur = conexion.cursor()
    cur.execute(f"SELECT * FROM users WHERE chat_id = {chat_id}")
    consulta = cur.fetchall()
    return consulta


def currentweather(params: dict):
    r = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    request = r.json()
    reply = weather.weathertext(request)
    bot.send_message(chat_id=chanel, text=f"#resumen: {request['weather'][0]['description']}  \n#main: {request['weather'][0]['main']}")
    return reply


def setlocation(update: Update, context: CallbackContext): # Recepción de locaciones de los usuarios
    global location
    global latitud
    global longitud

    latitud = []
    longitud = []

    params = {"q": "", "limit": "5", "appid": API}

    location = ' '.join(context.args)
    regex = re.compile("([a-z áéíóúüñ]+), ([a-z áéíóúüñ])", re.IGNORECASE) # regex para insertar ciudad en formato correcto
    m = regex.match(location)

    if m:
        # Poner localización
        params["q"] = location
        r = requests.get("http://api.openweathermap.org/geo/1.0/direct?", params=params)
        jsonfile = r.json()
        if len(jsonfile) == 0:
            update.message.reply_text("Parece que no hemos encontrado ninguna ciudad con ese nombre, lo sentimos mucho.")
        else:
            with open("ISO3166-1.json") as file:  # Abrir JSON con código de países.
                data = json.load(file)
                count = 1
                text = ""
                botton = []
                for city in jsonfile:
                    countstr = str(count)
                    botton.append(InlineKeyboardButton(countstr, callback_data=countstr))
                    latitud.append(city["lat"])
                    longitud.append(city["lon"])
                    text = text + "\n" + countstr + "." + " " + city["name"] + ","
                    if "state" in city:
                        text = text + " " + city["state"]
                    text = text + ":" + " " + data[city["country"]]
                    count += 1
            file.close()
            tecladociudades = [botton, [InlineKeyboardButton("Ninguna de estas.", callback_data="ciudad_no_encontrada")]]
            update.message.reply_text(f"<b>Selecciona tu ciudad:</b> \n{text}",
                                      reply_markup=InlineKeyboardMarkup(tecladociudades), parse_mode=ParseMode.HTML)

    else:
        update.message.reply_text("Parece que no ingresaste la ciudad correctamente. Usa el formato <b>'/setlocation Ciudad, País'.</b>", parse_mode=ParseMode.HTML)


def weathernow(update: Update, context: CallbackContext):
    consulta = consultbd(update.message.chat_id)
    if consulta[0][1] is not None:
        params = {"lat": consulta[0][2], "lon": consulta[0][3], "appid": API, "units": "metric", "lang": "es"}
        text_reply = currentweather(params)
        update.message.reply_text(text=text_reply)
    elif consulta[0][1] is None:
        update.message.reply_text("Parece que no has registrado ninguna ciudad, utiliza el comando /setlocation para eso.")
    else:
        update.message.reply_text("ERROR DESCONOCIDO")
        bot.send_message(chat_id=chanel, text="Error en comando Weathernow")


def button(update: Update, context: CallbackContext): # Callbacks de botones
    results = ["1", "2", "3", "4", "5"] # Posibles locaciones

    query = update.callback_query  # Esto es el callback de los botones

    # Teclado de configuración del perfil
    tecladomiperfil = [
        [InlineKeyboardButton("Cambiar Ciudad", callback_data="cambiarciudad")],
        [InlineKeyboardButton("Eliminar Perfil", callback_data="eliminarperfil")]
    ]
    # Botón del tiempo ahora
    botoniempo = [
        [InlineKeyboardButton("El tiempo ahora.", callback_data="weathernow")]
    ]
    # Botones de eliminación de perfil
    tecladoelimianrperfil = [
        [InlineKeyboardButton("Sí, estoy seguro.", callback_data="confirmareliminar")],
        [InlineKeyboardButton("No, no quiero.", callback_data="noeliminarperfil")]
    ]
    # Botones de donación
    tecladodonacion = [
        [InlineKeyboardButton("Bitcoin", callback_data="donar_bitcoin")],
        [InlineKeyboardButton("Toncoin", callback_data="donar_toncoin")]
    ]

    # Comprobación de los callbacks
    if query.data == "my perfil": # Envía los botones del perfil al usuario
        consulta = consultbd(query.message.chat_id)
        # query.message.reply_location(latitude=consulta[0][2], longitude=consulta[0][3])
        query.message.reply_photo(photo="https://iconos8.es/icon/Hj21JM30swCm/test-account", caption=f"<b>Aquí está tu perfil:</b> \nCiudad: {consulta[0][1]} \nPinWeather Pro: No disponible", reply_markup=InlineKeyboardMarkup(tecladomiperfil), parse_mode=ParseMode.HTML)

    elif query.data == "weathernow": # Consulta de tiempo por botón "El tiempo ahora"
        consulta = consultbd(query.message.chat_id)
        if consulta[0][1] is not None:
            params = {"lat": consulta[0][2], "lon": consulta[0][3], "appid": API, "units": "metric", "lang": "es"}
            text_reply = currentweather(params)
            query.message.reply_text(text=text_reply)
        elif consulta[0][1] is None:
            query.message.reply_text("Parece que <b>no has registrado ninguna ciudad</b>, utiliza el comando /setlocation para eso.", parse_mode=ParseMode.HTML)
        else:
            query.message.reply_text("ERROR DESCONOCIDO")
            bot.send_message(chat_id=chanel, text="Error en comando boton weathernow, callabck no registrado")

    elif query.data == "ciudad_no_encontrada": # Se envía si no hay coincidencias de la ciudad del ususario con la base de datos de la API
        query.message.reply_text("Intenta escribir la ubicación de otra forma o cambia el país por el estado, por ejemplo: /setlocation Miami, Florida.")

    elif query.data == "cambiarciudad": # Le dice a los usuarios como cambiar la ciudad
        consulta = consultbd(query.message.chat_id)
        query.message.reply_location(latitude=consulta[0][2], longitude=consulta[0][3])
        query.message.reply_text(f"Tu ciudad actual es <b>{consulta[0][1]}</b>. Para cambiar de ciudad solo tienes que utilizar el comando /setlocation seguido de la ciudad y el país.", parse_mode=ParseMode.HTML)

    elif query.data == "eliminarperfil":
        query.message.reply_text("¿Estás seguro que quieres eliminar tu perfil?", reply_markup=InlineKeyboardMarkup(tecladoelimianrperfil))

    elif query.data == "confirmareliminar": # Eliminación de perfil de la base de datos
        conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
        cur = conexion.cursor()
        cur.execute(f"BEGIN; DELETE FROM users WHERE chat_id = {query.message.chat.id}; \nCOMMIT")
        query.message.reply_text("Perfil Eliminado.")
        bot.send_message(chat_id=chanel, text="Un usuario eliminó su perfil")

    elif query.data == "noeliminarperfil":
        print("Ufff que alivio, te he cogido mucho aprecio.")

    elif query.data == "forecast":
        query.message.reply_text("Por ahora esta función no está disponible, estamos trabajando en ella.")

    elif query.data in results: # Envío de confirmación de ciudad registrada, mapa de ciudad y botón del tiempo
        long = longitud[int(query.data) - 1]
        lat = latitud[int(query.data) - 1]
        conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
        cur = conexion.cursor()
        cur.execute(
            f"BEGIN; UPDATE users \nSET \nlatitud = {lat}, longitud = {long}, \ncity = \'{location}\' \nWHERE chat_id = {query.message.chat.id}; \nCOMMIT")
        query.message.reply_text(f"Tu ciudad ha sido registrada: <b>{location}</b>.", parse_mode=ParseMode.HTML)
        query.message.reply_location(latitude=lat, longitude=long)
        query.message.reply_text("Con este botón puedes ver el tiempo en tu ciudad, <b>fíjalo para tenerlo siempre a mano</b>", reply_markup=InlineKeyboardMarkup(botoniempo), parse_mode=ParseMode.HTML)

    elif query.data == "donar":
        query.message.reply_text("Una donación ayuda a mantener el bot online todo el mes. Gracias por ayduar.", reply_markup=InlineKeyboardMarkup(tecladodonacion))

    elif query.data == "donar_bitcoin":
        query.message.reply_photo(photo="https://iconos8.es/icon/XDum8M4mrAZQ/bitcoin", caption=f"Esta es la Wallet para la donación de <b>Bitcoin</b>: <code>{bitcoin}</code>", parse_mode=ParseMode.HTML)

    elif query.data == "donar_toncoin":
        query.message.reply_photo(photo="https://seeklogo.com/images/T/toncoin-ton-logo-DBE22B2DFB-seeklogo.com.png", caption=f"Esta es la Wallet para la donación de <b>Toncoin</b>: <code>{toncoin}</code>", parse_mode=ParseMode.HTML)

    else:
        print(query.data)
        bot.send_message(chat_id=chanel, text=f"Error en Callback de botón: {query.data}")


def start(update: Update, context: CallbackContext):

    # Ver si el usuario está en la base de datos
    conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
    cur = conexion.cursor()
    cur.execute(f"SELECT chat_id FROM users WHERE chat_id = {update.message.chat_id}")
    consulta = cur.fetchall()

    if len(consulta) == 0:
        # Insertar usuario en la base de datos
        cur.execute(f"BEGIN; \nINSERT INTO users (chat_id) VALUES ({update.message.chat_id}); \nCOMMIT")
        print("Usuario añadido")
        update.message.reply_text(f"Hola envíame tu ciudad y pais de esta forma: \n"
                                  f"/setlocation London, United Kingdom")
        bot.send_message(chat_id=chanel, text="Nuevo Usuario Añadido")
    elif len(consulta) == 1:
        teclado = [
            [InlineKeyboardButton("Mi perfil", callback_data="my perfil")],
            [InlineKeyboardButton("El tiempo ahora", callback_data="weathernow")],
            [InlineKeyboardButton("Pronóstico", callback_data="forecast")],
            [InlineKeyboardButton("Donar", callback_data="donar")]
        ]
        reply_markup = InlineKeyboardMarkup(teclado)
        update.message.reply_text(f"Hola {update.message.from_user.first_name}, ¿qué quieres mirar?", reply_markup=reply_markup)

    else:
        print("ERROR")
        bot.send_message(chat_id=chanel, text="Error en comando Start")

    conexion.close()


def helpcommand(update: Update, context: CallbackContext):
    update.message.reply_text("Parece que necesitas ayuda, échale un vistazo a esto: \nhttps://telegra.ph/PinWeather-12-15")


if __name__ == '__main__':
    TOKEN = getenv("TOKEN_BOT")
    API = getenv("TOKEN_API")
    chanel = getenv("CHANEL")
    host = getenv("PGHOST")
    password = getenv("PGPASSWORD")
    database = getenv("PGDATABASE")
    bitcoin = getenv("BITCOIN")
    toncoin = getenv("TONCOIN")


    bot = Bot(TOKEN)
    bot.send_message(chat_id=chanel, text="Bot Iniciado")
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", callback=start))
    dp.add_handler(CommandHandler("setlocation", callback=setlocation))
    dp.add_handler(CommandHandler("weathernow", callback=weathernow))
    dp.add_handler(CommandHandler("help", callback=helpcommand))
    updater.dispatcher.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()
