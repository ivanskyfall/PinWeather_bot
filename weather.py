"""Recibe un float de la respuesta
de la API de la dirección del viento
y devuelve el punto cardinal correspondiente"""


def wind_direction(dirc):
    dirc = int(dirc)
    if dirc in range(0, 23):
        return "N\u2191"
    elif dirc in range(23, 68):
        return "NE\u2197"
    elif dirc in range(68, 113):
        return "E\u2192"
    elif dirc in range(113, 158):
        return "SE\u2198"
    elif dirc in range(158, 203):
        return "S\u2193"
    elif dirc in range(203, 248):
        return "SO\u2199"
    elif dirc in range(248, 293):
        return "O\u2190"
    elif dirc in range(293, 338):
        return "NO\u2196"
    elif dirc in range(338, 361):
        return "N\u2191"
    else:
        return None





"""
Arma el texto para enviarlo con la
información meteorlógica,
recibe un dic con la respuesta de la api
"""


def weathertext(request: dict):
    reply = f"Ciudad: {request['name']} " \
            f"\nResumen: {request['weather'][0]['description'].capitalize()}." \
            f"\nTemperatura: " \
            f"\n  Actual: {request['main']['temp']} ºC" \
            f"\n  Se siente como {request['main']['feels_like']} ºC" \
            f"\n  Mínima: {request['main']['temp_min']} ºC" \
            f"\n  Máxima: {request['main']['temp_max']} ºC" \
            f"\nViento: {round((request['wind']['speed'] * 3.6), 2)} km/h, con dirección {wind_direction(request['wind']['deg'])} " \
            f"\nNubosidad: {request['clouds']['all']}%" \

    if 'rain' in request and request['rain']['3h'] != 0:
        reply = reply + f"\n Lluvia en las últimas horas: {request['rain']['3h']}mm"
    elif 'snow' in request and request['snow']['3h'] != 0:
        reply = reply + f"\n Nieve en las últimas horas: {request['snow']['3h']}mm"
    elif 'rain' and 'snow' not in request:
        reply = reply + f"\nNo ha llovido o nevado en las últimas horas."

    reply = reply + f"\nPresión atmosférica: {request['main']['pressure']} hPa" \
                    f"\nHumedad relativa: {request['main']['humidity']}%"

    return reply


"""
reply = f"En {request['name']} hay {request['weather'][0]['description']}. La temperatura es de {request['main']['temp']} ºC," \
        f" que se sienten como {request['main']['feels_like']} ºC. La presión es de {request['main']['pressure']} hPa"\
        f" y la humedad relativa es del {request['main']['humidity']}%. El viento sopla a {request['wind']['speed']} m/s."

"""

