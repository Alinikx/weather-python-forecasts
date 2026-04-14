# weather_gui_.py

import json
import threading
from pathlib import Path
from datetime import datetime

import requests
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


APP_TITLE = "ADS Meteo GUI"
APP_GEOMETRY = "980x620"
REQUEST_TIMEOUT = 12
CONFIG_FILE = Path("weather_config.json")
ICON_SPRITE_FILE = Path("weather_icons.jpg")

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

# Coordinate nella sprite 4x4: (colonna, riga)
ICON_POSITIONS = {
    "cloud": (0, 0),
    "partly_cloudy": (1, 0),
    "overcast": (2, 0),
    "thunderstorm": (3, 0),

    "drizzle": (0, 1),
    "rain": (1, 1),
    "snow": (2, 1),
    "hail": (3, 1),

    "showers": (0, 2),
    "sun_showers": (1, 2),
    "sun": (2, 2),
    "sunrise": (3, 2),

    "moon": (0, 3),
    "fog": (1, 3),
    "drop": (2, 3),
    "umbrella": (3, 3),
}


def safe_get_json(url, *, params=None, timeout=REQUEST_TIMEOUT):
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def weather_code_to_text(code):
    return WMO_CODES.get(code, f"Codice {code}")


def weather_code_to_icon_key(code):
    if code == 0:
        return "sun"
    if code in (1, 2):
        return "partly_cloudy"
    if code == 3:
        return "overcast"
    if code in (45, 48):
        return "fog"
    if code in (51, 53, 55, 56, 57):
        return "drizzle"
    if code in (61, 63, 65, 66, 67):
        return "rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "snow"
    if code in (80, 81, 82):
        return "showers"
    if code in (95, 96, 99):
        return "thunderstorm"
    return "cloud"


def format_date_italian(date_str):
    weekday_names = [
        "Lunedì",
        "Martedì",
        "Mercoledì",
        "Giovedì",
        "Venerdì",
        "Sabato",
        "Domenica",
    ]

    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = weekday_names[dt.weekday()]
    return f"{weekday} {dt.strftime('%d-%m-%Y')}"


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
        code = weather_codes[i] if i < len(weather_codes) else None
        days.append({
            "date": format_date_italian(day),
            "condition": weather_code_to_text(code) if code is not None else "—",
            "weather_code": code,
            "tmax": tmax[i] if i < len(tmax) else "—",
            "tmin": tmin[i] if i < len(tmin) else "—",
            "rain_prob": pprob[i] if i < len(pprob) else "—",
            "sunrise": sunrise[i][-5:] if i < len(sunrise) and isinstance(sunrise[i], str) else "—",
            "sunset": sunset[i][-5:] if i < len(sunset) and isinstance(sunset[i], str) else "—",
        })

    current_code = current.get("weather_code")

    return {
        "current": {
            "temp_c": current.get("temperature_2m"),
            "feels_like_c": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_kmh": current.get("wind_speed_10m"),
            "precip_mm": current.get("precipitation"),
            "condition": weather_code_to_text(current_code),
            "weather_code": current_code,
        },
        "days": days,
    }


def average_rgb(values):
    count = len(values)
    return tuple(sum(v[i] for v in values) // count for i in range(3))


def remove_background_to_transparent(image, tolerance=18):
    image = image.convert("RGBA")
    w, h = image.size

    corners = [
        image.getpixel((0, 0))[:3],
        image.getpixel((w - 1, 0))[:3],
        image.getpixel((0, h - 1))[:3],
        image.getpixel((w - 1, h - 1))[:3],
    ]
    bg = average_rgb(corners)

    pixels = []
    for r, g, b, a in image.getdata():
        if (
            abs(r - bg[0]) <= tolerance and
            abs(g - bg[1]) <= tolerance and
            abs(b - bg[2]) <= tolerance
        ):
            pixels.append((r, g, b, 0))
        else:
            pixels.append((r, g, b, a))

    image.putdata(pixels)
    return image


def crop_to_visible_content(image, padding=6):
    alpha = image.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return image

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(image.width, right + padding)
    bottom = min(image.height, bottom + padding)

    return image.crop((left, top, right, bottom))


def fit_image_to_box(image, box_size):
    box_w, box_h = box_size
    image = image.copy()
    image.thumbnail((box_w, box_h), Image.LANCZOS)

    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    x = (box_w - image.width) // 2
    y = (box_h - image.height) // 2
    canvas.paste(image, (x, y), image)
    return canvas


def build_icon_images(sprite_path, icon_size=(24, 24)):
    if not sprite_path.exists():
        return {}

    sheet = Image.open(sprite_path).convert("RGBA")
    width, height = sheet.size

    cols = 4
    rows = 4
    cell_w = width // cols
    cell_h = height // rows

    icons = {}

    for key, (col, row) in ICON_POSITIONS.items():
        left = col * cell_w
        top = row * cell_h
        right = (col + 1) * cell_w
        bottom = (row + 1) * cell_h

        cell = sheet.crop((left, top, right, bottom))
        cell = remove_background_to_transparent(cell, tolerance=20)
        cell = crop_to_visible_content(cell, padding=max(4, min(cell_w, cell_h) // 20))
        cell = fit_image_to_box(cell, icon_size)

        icons[key] = ImageTk.PhotoImage(cell)

    return icons


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry(APP_GEOMETRY)
        self.minsize(700, 300)

        self.config_data = load_config()

        self.city_var = tk.StringVar(value=self.config_data.get("last_city", ""))
        self.location_var = tk.StringVar(value="—")
        self.status_var = tk.StringVar(value="Inserisci una città oppure usa l'ultima salvata.")
        self.current_var = tk.StringVar(value="Dati attuali: —")

        self.icon_images_small = build_icon_images(ICON_SPRITE_FILE, icon_size=(22, 22))
        self.icon_images_large = build_icon_images(ICON_SPRITE_FILE, icon_size=(50, 50))

        self._build_ui()

        last_city = self.config_data.get("last_city")
        if last_city:
            self.load_city(last_city)

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure("Treeview", rowheight=28)

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

        location_frame = ttk.Frame(info)
        location_frame.pack(anchor="w")

        ttk.Label(
            location_frame,
            text="Città:",
            font=("Segoe UI", 11, "bold")
        ).pack(side="left", padx=(0, 6))

        self.location_label = ttk.Label(
            location_frame,
            textvariable=self.location_var,
            font=("Segoe UI", 11, "bold"),
            compound="right"
        )
        self.location_label.pack(side="left")

        ttk.Label(info, textvariable=self.current_var, justify="left").pack(anchor="w", pady=(6, 0))
        ttk.Label(info, textvariable=self.status_var, foreground="#666").pack(anchor="w", pady=(6, 10))

        main = ttk.Labelframe(self, text="Previsioni giornaliere", padding=10)
        main.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("date", "tmin", "tmax", "rain", "sunrise", "sunset")
        self.tree = ttk.Treeview(main, columns=columns, show="tree headings", height=14)

        self.tree.heading("#0", text="Condizione")
        self.tree.heading("date", text="Data")
        self.tree.heading("tmin", text="Min °C")
        self.tree.heading("tmax", text="Max °C")
        self.tree.heading("rain", text="Pioggia %")
        self.tree.heading("sunrise", text="Alba")
        self.tree.heading("sunset", text="Tramonto")

        self.tree.column("#0", width=180, anchor="center")
        self.tree.column("date", width=180, anchor="center")
        self.tree.column("tmin", width=80, anchor="center")
        self.tree.column("tmax", width=80, anchor="center")
        self.tree.column("rain", width=90, anchor="center")
        self.tree.column("sunrise", width=90, anchor="center")
        self.tree.column("sunset", width=90, anchor="center")

        scrollbar = ttk.Scrollbar(main, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def set_status(self, text):
        self.after(0, lambda: self.status_var.set(text))

    def set_location_with_icon(self, text, weather_code=None):
        def _update():
            self.location_var.set(text)

            icon_key = weather_code_to_icon_key(weather_code) if weather_code is not None else None
            icon = self.icon_images_large.get(icon_key)

            self.location_label.configure(image=icon)
            self.location_label.image = icon

        self.after(0, _update)

    def set_current(self, text):
        self.after(0, lambda: self.current_var.set(text))

    def fill_days(self, days):
        def _update():
            for item in self.tree.get_children():
                self.tree.delete(item)

            for day in days:
                code = day.get("weather_code")
                icon_key = weather_code_to_icon_key(code) if code is not None else None
                icon = self.icon_images_small.get(icon_key)

                self.tree.insert(
                    "",
                    "end",
                    text=day["condition"],
                    image=icon,
                    values=(
                        day["date"],
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
            f"Percepita {current['feels_like_c']} °C\n"
            f"Precipitazione: {current['precip_mm']} mm    |    "
            f"Condizione: {current['condition']}\n"
            f"Umidità: {current['humidity']} %    |    "
            f"Vento: {current['wind_kmh']} km/h"
        )

        self.config_data["last_city"] = location["city"]
        save_config(self.config_data)

        self.set_location_with_icon(location["label"], current["weather_code"])
        self.set_current(current_text)
        self.fill_days(weather["days"])
        self.set_status("Aggiornato.")

    def run(self):
        self.mainloop()


if __name__ == "__main__":
    app = WeatherApp()
    app.run()
