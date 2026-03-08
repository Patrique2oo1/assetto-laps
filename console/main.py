import json

# użyte funkcje
# konwersja czasów okrążeń na format MM:SS.mmm
def convert_time(seconds):
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{minutes:02}:{secs:02}.{millis:03}"

# odczyt daty rozegrania sesji
def get_date(file, source_json):
    # pobranie nazwy pliku
    filename = file.split("\\")[-1]
    if "-" in filename:
        # pobranie daty w formacie YY-MM-DD
        date_part = filename.split("-")[0]
        if len(date_part) == 6 and date_part.isdigit():
            return f"20{date_part[0:2]}-{date_part[2:4]}-{date_part[4:6]}"
    return "no data"
    
# odczyt parametrów dot. warunków atmosferycznych
def get_weather(weather, section, key):
    tag = f"[{section}]"
    if tag not in weather:
        return "?"
    part = weather.split(tag, 1)[1]
    if key + "=" not in part:
        return "?"
    return part.split(key + "=", 1)[1].split("\n", 1)[0].strip()
    

# wczytanie pliku JSON
file = input("Proszę wprowadzić ścieżkę do pliku JSON z wynikami sesji: ")

try:
    with open(file, 'r', encoding="utf-8") as content:
        source_json = json.load(content)
except FileNotFoundError:
    print("Nie znaleziono pliku!")
    exit()
except json.JSONDecodeError:
    print("Dany plik jest w nieprawidłowym formacie!")
    exit()
    

# wypisanie informacji o sesji
# 1. samochód
# 2. tor
# 3. data
try:
    print(f"car: {source_json['players'][0]['car']}")
    print(f"track name: {source_json['track']}")
    print(f"date: {get_date(file, source_json)}")

    # wydobycie informacji o warunkach atmosferycznych
    weather = source_json.get("__raceIni", "").replace("\r\n", "\n")

    weather_name = get_weather(weather, "WEATHER", "NAME")
    ambient_temp = get_weather(weather, "TEMPERATURE", "AMBIENT")
    track_temp = get_weather(weather, "TEMPERATURE", "ROAD")
    wind_min = get_weather(weather, "WIND", "SPEED_KMH_MIN")
    wind_max = get_weather(weather, "WIND", "SPEED_KMH_MAX")
    wind_dir = get_weather(weather, "WIND", "DIRECTION_DEG")
    sun_time = get_weather(weather, "LIGHTING", "SUN_ANGLE")

    # wypisanie warunków atmosferycznych
    print("\nconditions:")
    print(f"weather:        {weather_name}")
    print(f"air temp:       {ambient_temp} °C")
    print(f"track temp:     {track_temp} °C")
    print(f"wind:           {wind_min}–{wind_max} km/h from {wind_dir}°")
    print(f"sun position:   {sun_time}°")
    print()

    # dla każdego kierowcy - wypisanie czasów sektorów, okrążeń oraz najszybszych sektorów i okrążeń
    players = source_json['players']

    # wybór sesji
    for session in source_json['sessions']:
        if session['type'] in (3, 1):
            wanted_session = session
        if session['type'] == 3:
            break

    for player in players:
        # pominięcie kierowców bez nazwy
        if not player['name'].strip():
            continue
            
        print(f"driver: {player['name']}")

        best_sectors = [float('inf'), float('inf'), float('inf')]
        best_lap = float('inf')
    
        # ID auta jako indeks w "players"
        car_id = players.index(player)  
        
        for lap in wanted_session['laps']:
            # sprawdzenie czy dane okrążenie nie należy do danego kierowcy
            if lap['car'] != car_id:
                continue
            
            # sprawdzenie czy okrążenie składa się z 3 sektorów
            if len(lap['sectors']) < 3:
                print(f"lap: {lap['lap']+1:2d} | no data")
                continue
            # zamiana czasów sektorów na sekundy
            sectors = [lap['sectors'][0]/1000, lap['sectors'][1]/1000, lap['sectors'][2]/1000]
            lap_seconds = sectors[0] + sectors[1] + sectors[2]

            # sprawdzenie czy dany sektor jest najszybszym sektorem kierowcy
            for i in range(3):
                if sectors[i] < best_sectors[i]:
                    best_sectors[i] = sectors[i]

            # sprawdzenie czy dane okrążenie jest najszybszym okrążeniem kierowcy
            if lap_seconds < best_lap:
                best_lap = lap_seconds
        
            # wypisanie czasów sektorów oraz okrążeń w formacie MM:SS.mmm
            print(
                f"lap: {lap['lap']+1:2d} | "
                f"sectors: [{sectors[0]:>7.3f}, {sectors[1]:>7.3f}, {sectors[2]:>7.3f}] | "
                f"time: {convert_time(lap_seconds)}"
            )
    
        # jeśli best_lap nie zostało zaktualizowane, to kierowca nie pokonał żadnego okrążenia
        if best_lap == float('inf'):
            print("best lap: no data")
            print("best sectors: no data")
        else:
            print("best lap:", convert_time(best_lap))
            best_total = convert_time(best_sectors[0] + best_sectors[1] + best_sectors[2])
            print(
                f"best sectors: [{best_sectors[0]:>7.3f}, {best_sectors[1]:>7.3f}, {best_sectors[2]:>7.3f}] | "
                f"best time: {best_total}"
            )

        print("==================\n")
except KeyError as e:
    print(f"Brak klucza: {e}")
    exit()
except IndexError as e:
    print(f"Brak wymaganych danych: {e}")
    exit()
