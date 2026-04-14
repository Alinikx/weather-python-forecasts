# weather_gui_.py

import json
import threading
from pathlib import Path

import requests
import tkinter as tk
from tkinter import ttk, messagebox


APP_TITLE = "Meteo GUI"
APP_GEOMETRY = "800x400"
REQUEST_TIMEOUT = 12
CONFIG_FILE = Path("weather_config.json")

OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


WMO_CODES = {
    0: "Sereno",
    1: "Prevalentemente sereno",
    2: "Parzialmente nuvoloso",
    3: "Coperto",
    45: "Nebbia",
    48: "Nebbia con brina",
    51: "Pioviggine debole",
    53: "Pioviggine moderata",
    55: "Pioviggine intensa",
    56: "Pioviggine gelata debole",
    57: "Pioviggine gelata intensa",
    61: "Pioggia debole",
    63: "Pioggia moderata",
    65: "Pioggia intensa",
    66: "Pioggia gelata debole",
    67: "Pioggia gelata intensa",
    71: "Neve debole",
    73: "Neve moderata",
    75: "Neve intensa",
    77: "Granuli di neve",
    80: "Rovesci deboli",
    81: "Rovesci moderati",
    82: "Rovesci intensi",
    85: "Rovesci di neve deboli",
    86: "Rovesci di neve intensi",
    95: "Temporale",
    96: "Temporale con grandine debole",
    99: "Temporale con grandine forte",
}


def safe_get_json(url, *, params=None, timeout=REQUEST_TIMEOUT):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def weather_code_to_text(code):
    return WMO_CODES.get(code, f"Codice {code}")


def load_config():
    if not CONFIG_FILE.exists():
        return {}
    try:
        with CONFIG_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    with CONFIG_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def geocode_city(city_name):
    params = {
        "name": city_name,
        "count": 1,
        "language": "it",
        "format": "json",
    }
    data = safe_get_json(OPEN_METEO_GEOCODING_URL, params=params)
    results = data.get("results", [])

    if not results:
        raise RuntimeError(f"Città non trovata: {city_name}")

    r = results[0]
    name = r.get("name", city_name)
    admin1 = r.get("admin1")
    country = r.get("country")

    label_parts = [name]
    if admin1:
        label_parts.append(admin1)
    if country:
        label_parts.append(country)

    return {
        "city": name,
        "label": ", ".join(label_parts),
        "latitude": float(r["latitude"]),
        "longitude": float(r["longitude"]),
    }


def fetch_weather_openmeteo(lat, lon):
    params = {
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "forecast_days": 7,
        "current": ",".join([
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "sunrise",
            "sunset",
        ]),
    }

    data = safe_get_json(OPEN_METEO_FORECAST_URL, params=params)
    current = data.get("current", {})
    daily = data.get("daily", {})

    days = []
    times = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    tmax = daily.get("temperature_2m_max", [])
    tmin = daily.get("temperature_2m_min", [])
    pprob = daily.get("precipitation_probability_max", [])
    sunrise = daily.get("sunrise", [])
    sunset = daily.get("sunset", [])

    for i, day in enumerate(times):
        days.append({
            "date": day,
            "condition": weather_code_to_text(weather_codes[i]) if i < len(weather_codes) else "—",
            "tmax": tmax[i] if i < len(tmax) else "—",
            "tmin": tmin[i] if i < len(tmin) else "—",
            "rain_prob": pprob[i] if i < len(pprob) else "—",
            "sunrise": sunrise[i][-5:] if i < len(sunrise) and isinstance(sunrise[i], str) else "—",
            "sunset": sunset[i][-5:] if i < len(sunset) and isinstance(sunset[i], str) else "—",
        })

    return {
        "current": {
            "temp_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
            "precip_mm": current.get("precipitation"),
            "condition": weather_code_to_text(current.get("weather_code")),
        },
        "days": days,
    }


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(860, 560)

        self.config_data = load_config()

        self.city_var = tk.StringVar(value=self.config_data.get("last_city", ""))
        self.location_var = tk.StringVar(value="Posizione: —")
        self.status_var = tk.StringVar(value="Inserisci una città oppure usa l'ultima salvata.")
        self.current_var = tk.StringVar(value="Dati attuali: —")

        self._build_ui()

        last_city = self.config_data.get("last_city")
        if last_city:
            self.load_city(last_city)

    def _build_ui(self):
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Città:").pack(side="left")

        entry = ttk.Entry(top, textvariable=self.city_var, width=34)
        entry.pack(side="left", padx=(8, 8))
        entry.bind("<Return>", lambda event: self.search_city())

        ttk.Button(top, text="Cerca", command=self.search_city).pack(side="left")
        ttk.Button(top, text="Usa ultima città", command=self.load_last_city).pack(side="left", padx=(8, 0))

        info = ttk.Frame(self, padding=(10, 0))
        info.pack(fill="x")

        ttk.Label(info, textvariable=self.location_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(info, textvariable=self.current_var, justify="left").pack(anchor="w", pady=(6, 0))
        ttk.Label(info, textvariable=self.status_var, foreground="#666").pack(anchor="w", pady=(6, 10))

        main = ttk.Labelframe(self, text="Previsioni giornaliere", padding=10)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("date", "condition", "tmin", "tmax", "rain", "sunrise", "sunset")
        self.tree = ttk.Treeview(main, columns=columns, show="headings", height=16)

        self.tree.heading("date", text="Data")
        self.tree.heading("condition", text="Condizione")
        self.tree.heading("tmin", text="Min °C")
        self.tree.heading("tmax", text="Max °C")
        self.tree.heading("rain", text="Pioggia %")
        self.tree.heading("sunrise", text="Alba")
        self.tree.heading("sunset", text="Tramonto")

        self.tree.column("date", width=110, anchor="center")
        self.tree.column("condition", width=250, anchor="w")
        self.tree.column("tmin", width=80, anchor="center")
        self.tree.column("tmax", width=80, anchor="center")
        self.tree.column("rain", width=80, anchor="center")
        self.tree.column("sunrise", width=80, anchor="center")
        self.tree.column("sunset", width=80, anchor="center")

        scrollbar = ttk.Scrollbar(main, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def set_location(self, text):
        self.after(0, lambda: self.location_var.set(text))

    def set_current(self, text):
        self.after(0, lambda: self.current_var.set(text))

    def fill_days(self, days):
        def _update():
            for item in self.tree.get_children():
                self.tree.delete(item)

            for day in days:
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        day["date"],
                        day["condition"],
                        day["tmin"],
                        day["tmax"],
                        day["rain_prob"],
                        day["sunrise"],
                        day["sunset"],
                    ),
                )
        self.after(0, _update)

    def run_in_thread(self, target):
        threading.Thread(target=self._safe_runner, args=(target,), daemon=True).start()

    def _safe_runner(self, target):
        try:
            target()
        except Exception as exc:
            self.set_status(f"Errore: {exc}")
            self.after(0, lambda: messagebox.showerror("Errore", str(exc)))

    def search_city(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showwarning("Attenzione", "Inserisci il nome di una città.")
            return

        self.load_city(city)

    def load_last_city(self):
        last_city = self.config_data.get("last_city")
        if not last_city:
            messagebox.showinfo("Info", "Non c'è ancora nessuna città salvata.")
            return

        self.city_var.set(last_city)
        self.load_city(last_city)

    def load_city(self, city):
        self.run_in_thread(lambda: self._load_city_worker(city))

    def _load_city_worker(self, city):
        self.set_status(f"Ricerca coordinate per {city}...")
        location = geocode_city(city)

        self.set_status(f"Download previsioni per {location['label']}...")
        weather = fetch_weather_openmeteo(location["latitude"], location["longitude"])

        current = weather["current"]
        current_text = (
            f"Temperatura: Attuale {current['temp_c']} °C    |    "
            f"Percepita {current['feels_like_c']} °C        \n"
            f"Precipitazione: {current['precip_mm']} mm    |    "
            f"Condizione: {current['condition']}\n"
            f"Umidità: {current['humidity']} %    |    "
            f"Vento: {current['wind_kmh']} km/h"
        )

        self.config_data["last_city"] = location["city"]
        save_config(self.config_data)

        self.set_location(f"Posizione: {location['label']}")
        self.set_current(current_text)
        self.fill_days(weather["days"])
        self.set_status("Aggiornato.")


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()