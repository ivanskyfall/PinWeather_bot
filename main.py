from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot, ParseMode
from telegram.ext import Updater, CallbackContext, CommandHandler, CallbackQueryHandler
from os import getenv
import psycopg2
import json
import requests
import re


location, latitud, longitud = '', [], []


def consultbd(chat_id):
    conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
    cur = conexion.cursor()
    cur.execute(f"SELECT * FROM users WHERE chat_id = {chat_id}")
    consulta = cur.fetchall()
    return consulta


def currentweather(params: dict):
    r = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    request = r.json()
    reply = f"En {request['name']} hay {request['weather'][0]['description']}. La temperatura es de {request['main']['temp']} ºC," \
            f" que se sienten como {request['main']['feels_like']} ºC. La presión es de {request['main']['pressure']} hPa"\
            f" y la humedad relativa es del {request['main']['humidity']}%. El viento sopla a {request['wind']['speed']} m/s."
    bot.send_message(chat_id=chanel, text=f"#resumen {request['weather'][0]['description']}")
    return reply


def setlocation(update: Update, context: CallbackContext):
    global location
    global latitud
    global longitud

    latitud = []
    longitud = []

    params = {"q": "", "limit": "5", "appid": API}

    location = ' '.join(context.args)
    regex = re.compile("([a-z áéíóúüñ]+), ([a-z áéíóúüñ])", re.IGNORECASE)
    m = regex.match(location)

    if m:
        # Poner localización
        params["q"] = location
        r = requests.get("http://api.openweathermap.org/geo/1.0/direct?", params=params)
        jsonfile = r.json()
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
                text = text + "\n" + countstr + "." + " " + city["name"] + "," + " " + data[city["country"]]
                if "state" in city:
                    text = text + ":" + " " + city["state"]
                count += 1
        file.close()
        tecladociudades = [botton]
        update.message.reply_text(f"<b>Selecciona tu ciudad:</b> \n{text}",
                                  reply_markup=InlineKeyboardMarkup(tecladociudades), parse_mode=ParseMode.HTML)
    else:
        update.message.reply_text("Parece que no ingresaste la ciudad correctamente. Usa el formato <b>'/setlocation Ciudad, País'.</b>", parse_mode=ParseMode.HTML)


def weathernow(update: Update, context: CallbackContext):
    consulta = consultbd(update.message.chat_id)
    if consulta[0][1] is not None:
        paramas = {"lat": consulta[0][2], "lon": consulta[0][3], "appid": API, "units": "metric", "lang": "es"}
        text_reply = currentweather(paramas)
        update.message.reply_text(text=text_reply)
    elif consulta[0][1] is None:
        update.message.reply_text("Parece que no has registrado ninguna ciudad, utiliza el comando /setlocation para eso.")
    else:
        update.message.reply_text("ERROR DESCONOCIDO")
        bot.send_message(chat_id=chanel, text="Error en comando Weathernow")


def button(update: Update, context: CallbackContext):
    results = ["1", "2", "3", "4", "5"]

    query = update.callback_query  # Esto es el callback de los botones

    # Teclado de configuración del perfil
    tecladomiperfil = [
        [InlineKeyboardButton("Cambiar Ciudad", callback_data="cambiarciudad")],
        [InlineKeyboardButton("Eliminar Perfil", callback_data="eliminarperfil")]
    ]
    botoniempo = [
        [InlineKeyboardButton("El tiempo ahora.", callback_data="weathernow")]
    ]
    tecladoelimianrperfil = [
        [InlineKeyboardButton("Sí, estoy seguro.", callback_data="confirmareliminar")],
        [InlineKeyboardButton("No, no quiero.", callback_data="noeliminarperfil")]
    ]

    # Comprobación de los callbacks
    if query.data == "my perfil":
        consulta = consultbd(query.message.chat_id)
        # query.message.reply_location(latitude=consulta[0][2], longitude=consulta[0][3])
        query.message.reply_photo(photo="https://iconos8.es/icon/Hj21JM30swCm/test-account", caption=f"<b>Aquí está tu perfil:</b> \nCiudad: {consulta[0][1]} \nPinWeather Pro: No disponible", reply_markup=InlineKeyboardMarkup(tecladomiperfil), parse_mode=ParseMode.HTML)

    elif query.data == "weathernow":
        consulta = consultbd(query.message.chat_id)
        if consulta[0][1] is not None:
            params = {"lat": consulta[0][2], "lon": consulta[0][3], "appid": API, "units": "metric", "lang": "es"}
            text_reply = currentweather(params)
            query.message.reply_text(text=text_reply)
        elif consulta[0][1] is None:
            query.message.reply_text("Parece que <b>no has registrado ninguna ciudad</b>, utiliza el comando /setlocation para eso.", parse_mode=ParseMode.HTML)
        else:
            query.message.reply_text("ERROR DESCONOCIDO")
            bot.send_message(chat_id=chanel, text="Error en comando boton weathernow, excepción desconocida")

    elif query.data == "cambiarciudad":
        consulta = consultbd(query.message.chat_id)
        query.message.reply_location(latitude=consulta[0][2], longitude=consulta[0][3])
        query.message.reply_text(f"Tu ciudad actual es <b>{consulta[0][1]}</b>. Para cambiar de ciudad solo tienes que utilizar el comando /setlocation seguido de la ciudad y el país.", parse_mode=ParseMode.HTML)

    elif query.data == "eliminarperfil":
        query.message.reply_text("¿Estás seguro que quieres eliminar tu perfil?", reply_markup=InlineKeyboardMarkup(tecladoelimianrperfil))

    elif query.data == "confirmareliminar":
        conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
        cur = conexion.cursor()
        cur.execute(f"BEGIN; DELETE FROM users WHERE chat_id = {query.message.chat.id}; \nCOMMIT")
        query.message.reply_text("Perfil Eliminado.")
        bot.send_message(chat_id=chanel, text="Un usuario eliminó su perfil")

    elif query.data == "noeliminarperfil":
        print("Ufff que alivio, te he cogido mucho aprecio.")

    elif query.data == "forecast":
        query.message.reply_text("Por ahora esta función no está disponible, estamos trabajando en ella.")

    elif query.data in results:
        long = longitud[int(query.data) - 1]
        lat = latitud[int(query.data) - 1]
        conexion = psycopg2.connect(host=host, database=database, user="postgres", password=password)
        cur = conexion.cursor()
        cur.execute(
            f"BEGIN; UPDATE users \nSET \nlatitud = {lat}, longitud = {long}, \ncity = \'{location}\' \nWHERE chat_id = {query.message.chat.id}; \nCOMMIT")
        query.message.reply_text(f"Tu ciudad ha sido registrada: <b>{location}</b>.", parse_mode=ParseMode.HTML)
        query.message.reply_location(latitude=lat, longitude=long)
        query.message.reply_text("Con este botón puedes ver el tiempo en tu ciudad, <b>fíjalo para tenerlo siempre a mano</b>", reply_markup=InlineKeyboardMarkup(botoniempo), parse_mode=ParseMode.HTML)

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
