# Dashboard.py

import database, os, re
from datetime import datetime, timezone, timedelta
from flask import Flask, render_template
from collections import OrderedDict
import ast

base_dir = '../files/web'
count_dir = '../ignore/count'

app = Flask(__name__, template_folder=os.path.join(base_dir, 'templates'), static_folder=os.path.join(base_dir, 'static'))
app.config['ACTIVE_ALERTS'] = []


def read_from_file(filename):
    """
    Read an integer from a file.

    If the file exists and contains an integer, return that integer.
    If the file does not exist or is empty, return 0.

    Parameters:
        filename (str): The name of the file to read from.

    Returns:
        int: The integer read from the file or 0 if file not found or empty.
    """
    if filename not in ("TOR Total.txt", "SVR Total.txt", "TOR Watch.txt", "SVR Watch.txt", "FFW Total.txt", "SPS.txt"):
        return "Invalid filename"

    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                return int(content)
            return 0
    except FileNotFoundError:
        return 0


@app.route('/')
def index():
    """
    The index function handles HTTP GET requests to the root URL ('/').
    
    It fetches and updates alerts, reads various alert totals from files, 
    and renders the index.html template with the active alerts and alert totals.
    
    Returns:
        The rendered index.html template with the active alerts and alert totals.
    """
    fetch_and_update_alerts()
    
    active_alerts = app.config.get('ACTIVE_ALERTS', [])

    TOR_total = read_from_file(os.path.join(count_dir, 'TOR Total.txt'))
    SVR_total = read_from_file(os.path.join(count_dir, 'SVR Total.txt'))
    FFW_total = read_from_file(os.path.join(count_dir, 'FFW Total.txt'))
    TOA = read_from_file(os.path.join(count_dir, 'TOA.txt'))
    SVA = read_from_file(os.path.join(count_dir, 'SVA.txt'))
    SPS = read_from_file(os.path.join(count_dir, 'SPS.txt'))
    Non_SPS_Total = read_from_file(os.path.join(count_dir, 'Non SPS Total.txt'))

    return render_template('index.html', active_alerts=active_alerts, TOR_total=TOR_total, SVR_total=SVR_total, FFW_total=FFW_total, TOA=TOA, SVA=SVA, SPS=SPS, Non_SPS_Total=Non_SPS_Total)

ALERT_PRIORITY = OrderedDict([
    ('Tornado Warning', 1),
    ('Severe Thunderstorm Warning', 2),
    ('Flash Flood Warning', 3),
    ('Tornado Watch', 4),
    ('Severe Thunderstorm Watch', 5),
    ('Special Weather Statement', 6)
])


def sort_alerts(alerts):
    """
    Sorts a list of alerts based on their priority.

    Args:
        alerts (list): A list of alert dictionaries.

    Returns:
        list: A sorted list of alert dictionaries.
    """
    sorted_alerts = sorted(alerts, key=lambda x: ALERT_PRIORITY.get(x['event'], float('inf')))
    return sorted_alerts


def get_timezone_keyword(offset):
    """
    Returns the timezone keyword for a given offset.

    Parameters:
        offset (timedelta): The timezone offset.

    Returns:
        str: The timezone keyword if found, otherwise the offset as a string.
    """
    offset_to_keyword = {
        timedelta(hours=-4): 'EDT',
        timedelta(hours=-5): 'CDT',
        timedelta(hours=-6): 'MDT',
        timedelta(hours=-7): 'PDT',
        timedelta(hours=-9): 'AKDT',
        timedelta(hours=-10): 'HST',
        
        timedelta(hours=-3): 'ADT',
        timedelta(hours=+10): 'CHST',
        timedelta(hours=+11): 'SAMT'
    }

    timezone_keyword = offset_to_keyword.get(offset)
    if timezone_keyword is None:
        return str(offset)
    else:
        return timezone_keyword


def fetch_and_update_alerts():
    """
    Fetches and updates alerts from the database.

    This function retrieves all alerts from the database, processes each alert to extract relevant information,
    and updates the active alerts list. It also removes expired alerts from the database.

    Parameters:
        None

    Returns:
        None
    """
    active_alerts = []
    alerts = database.get_all_alerts(table_name='alerts')
    current_time = datetime.now(timezone.utc)
    for alert in alerts:
        identifier, sent_datetime_str, expires_datetime_str, properties_str = alert

        expires_datetime = datetime.strptime(expires_datetime_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        properties = ast.literal_eval(properties_str)  # Convert the string back to a dictionary

        alert_endtime = properties["expires"]
        alert_endtime_tz_offset = alert_endtime[-6:]  # Extract the timezone offset from the string
        alert_endtime_naive = datetime.strptime(alert_endtime[:-6], "%Y-%m-%dT%H:%M:%S")  # Parse the datetime part without the offset

        # Create a timezone object from the offset
        offset_hours = int(alert_endtime_tz_offset[:3])
        offset_minutes = int(alert_endtime_tz_offset[4:])
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        alert_endtime_tz = timezone(offset)

        # Localize the naive datetime using the timezone offset
        expires_datetime_localized = alert_endtime_naive.replace(tzinfo=alert_endtime_tz)

        thunderstorm_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("thunderstormDamageThreat", ""))
        tornado_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("tornadoDamageThreat", ""))
        tornado_detection = clean_and_capitalize(properties.get("parameters", {}).get("tornadoDetection", ""))
        flash_flood_damage_threat = clean_and_capitalize(properties.get("parameters", {}).get("flashFloodDamageThreat", ""))

        if expires_datetime > current_time:
            event = properties["event"]
            messagetype = properties["messageType"]
            wfo = properties["senderName"]

            parameters = properties["parameters"]
            maxwind = clean_and_capitalize(parameters.get("maxWindGust"))
            maxhail = clean_and_capitalize(parameters.get("maxHailSize"))
            nwsheadline = clean_string(parameters.get("NWSheadline"))
            FFdetection = clean_and_capitalize(parameters.get("flashFloodDetection"))


            description = ''

            if messagetype == 'Update':
                if description != '':
                    description += f", UPDATE"
                else:
                    description += "UPDATE"

            if nwsheadline != 'None':
                if description != '':
                    description += f", NWS Headline: {nwsheadline}"
                else:
                    description += f"NWS Headline: {nwsheadline}"

            if thunderstorm_damage_threat:
                if description != '':
                    description += f", Thunderstorm Damage Threat: {(thunderstorm_damage_threat)}"
                else:
                    description += f"Thunderstorm Damage Threat: {(thunderstorm_damage_threat)}"

            if tornado_damage_threat:
                if description != '':
                    description += f", Tornado Damage Threat: {(tornado_damage_threat)}"
                else:
                    description += f"Tornado Damage Threat: {(tornado_damage_threat)}"

            if tornado_detection:
                if description != '':
                    description += f", Tornado Detection: {(tornado_detection)}"
                else:
                    description += f"Tornado Detection: {(tornado_detection)}"

            if flash_flood_damage_threat:
                if description != '':
                    description += f", Flash Flood Damage Threat: {(flash_flood_damage_threat)}"
                else:
                    description += f"Flash Flood Damage Threat: {(flash_flood_damage_threat)}"

            if maxwind != 'None':
                if description != '':
                    description += f", Max Wind: {(maxwind)}"
                else:
                    description += f"Max Wind: {(maxwind)}"
            
            if maxhail != 'None':
                if description != '':
                    description += f", Max Hail: {(maxhail)}"
                else:
                    description += f"Max Hail: {(maxhail)}"

            if FFdetection != 'None':
                if description != '':
                    description += f", Flash Flood Detection: {(FFdetection)}"
                else:
                    description += f"Flash Flood Detection: {(FFdetection)}"

            timezone_keyword = get_timezone_keyword(offset)
            formatted_expires_datetime = expires_datetime_localized.strftime(f"%B %d, %Y %I:%M %p {timezone_keyword}")

            area_desc = properties["areaDesc"]
            active_alerts.append({
                "event": event,
                "wfo": wfo,
                "description": description,
                "expiration": formatted_expires_datetime,
                "area": area_desc
            })
        else:
            database.remove_alert(identifier=identifier, table_name='alerts')

    sorted_alerts = sort_alerts(active_alerts)

    with app.app_context():
        app.config['ACTIVE_ALERTS'] = sorted_alerts


def clean_and_capitalize(value):
    """
    Cleans and capitalizes a given value by removing unwanted characters and converting it to title case.

    Args:
        value (str or list): The value to be cleaned and capitalized. Can be a string or a list of strings.

    Returns:
        str: The cleaned and capitalized string.
    """
    if isinstance(value, list):
        string = ''.join(str(item) for item in value)
    else:
        string = str(value)
    
    if not string:
        return ""
    
    cleaned_string = re.sub(r'[\[\]\'\"]', '', string)
    return cleaned_string.capitalize()


def clean_string(value):
    """
    This function cleans a given string by removing any list or dictionary 
    characters and returning it as a string. It takes one parameter, 'value', 
    which can be a string or a list of strings. It returns an empty string if 
    the input is empty, otherwise it returns the cleaned string.
    """
    if isinstance(value, list):
        string = ''.join(str(item) for item in value)
    else:
        string = str(value)
    
    if not string:
        return ""
    
    cleaned_string = re.sub(r'[\[\]\'\"]', '', string)    
    return cleaned_string


def update_active_alerts():
    """
    Updates the list of active alerts by fetching and updating the alerts within the application context.
    
    Parameters:
    None
    
    Returns:
    None
    """
    with app.app_context():
        fetch_and_update_alerts()

if __name__ == '__main__':
    app.run(host = 'localhost', port = 5000)
