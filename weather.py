import requests


def weathertext(params: dict):
    r = requests.get("https://api.openweathermap.org/data/2.5/weather", params=params)
    request = r.json()
    reply = f"Ciudad: {request['name']} " \
            f"\nResumen: {request['weather'][0]['description'].capitalize()} " \
            f"\nTemperatura: " \
            f"\n  Actual: {request['main']['temp']} ºC " \
            f"\n  Se siente como {request['main']['feels_like']} ºC " \
            f"\n  Mínima: {request['main']['temp_min']} ºC " \
            f"\n  Máxima: {request['main']['temp_max']} ºC" \
            f"\nViento: {round((request['wind']['speed'] * 3.6), 2)} km/h" \
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
