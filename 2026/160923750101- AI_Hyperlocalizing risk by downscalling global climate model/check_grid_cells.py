
import requests

locations = {
    "Central Hyderabad": (17.3850, 78.4867),
    "Secunderabad": (17.4399, 78.4983),
    "Gachibowli": (17.4401, 78.3489),
    "Miyapur": (17.4968, 78.3560),
    "Kukatpally": (17.4849, 78.4138),
    "LB Nagar": (17.3457, 78.5522),
    "Uppal": (17.4016, 78.5591),
    "Madhapur": (17.4483, 78.3915),
    "Charminar": (17.3616, 78.4747),
    "Shamshabad": (17.2403, 78.4294)
}

url = "https://api.open-meteo.com/v1/forecast"

print("CHECKING WEATHER GRID LOCATIONS\n")

for name, (lat, lon) in locations.items():

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "timezone": "Asia/Kolkata"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()

        print(name)
        print("Requested:", lat, lon)
        print("Grid used:", data["latitude"], data["longitude"])
        print("-" * 40)

    except requests.exceptions.RequestException as error:
        print("Error:", name, error)
