import requests, json, time, os, pystray, threading, alerts, database, atexit, pytz, datetime
from datetime import datetime, timezone
from plyer import notification
from PIL import Image
from dateutil import parser, tz
from apscheduler.schedulers.background import BackgroundScheduler
from dashboard import app, update_active_alerts

database.create_table()

if os.path.exists('warnings'):
    for f in os.listdir('warnings'):
        os.remove(os.path.join('warnings', f))
    os.removedirs('warnings')
if os.path.exists('count'):
    for f in os.listdir('count'):
        os.remove(os.path.join('count', f))
    os.removedirs('count')

if not os.path.exists('warnings'):
    os.makedirs('warnings')
if not os.path.exists('count'):
    os.makedirs('count')

warning_files = {
    'Alert Total.txt': 'Total Alerts: 0',
    'Non SPS Total.txt': 'Non-SPS Alerts: 0',

    'TOR Total.txt': 'Active Tornado Warnings: 0',
    'TOR.txt': 'Tornado Warnings: 0',
    'TORR.txt': 'Confirmed Tornado Warnings: 0',
    'TORP.txt': 'PDS Tornado Warnings: 0',
    'TORE.txt': 'Tornado Emergencies: 0',

    'SVR Total.txt': 'Active Severe Thunderstorm Warnings: 0',
    'SVR.txt': 'Severe Thunderstorm Warnings: 0',
    'SVRC.txt': 'Considerable Severe Thunderstorm Warnings: 0',
    'SVRD.txt': 'Destructive Severe Thunderstorm Warnings: 0',
    'SVRTOR.txt': 'Tornado Possible Severe Thunderstorm Warnings: 0',

    'FFW Total.txt': 'Active Flash Flood Warnings: 0',
    'FFW.txt': 'Flash Flood Warnings: 0',
    'FFWC.txt': 'Considerable Flash Flood Warnings: 0',
    'FFE.txt': 'Flash Flood Emergencies: 0',

    'TOA.txt': 'Tornado Watches: 0',
    'SVA.txt': 'Severe Thunderstorm Watches: 0',

    'SPS.txt': 'Special Weather Statements: 0'
}

warning_count_files = {
    'Alert Total.txt': '0',
    'Non SPS Total.txt': '0',

    'TOR Total.txt': '0',
    'TOR.txt': '0',
    'TORR.txt': '0',
    'TORP.txt': '0',
    'TORE.txt': '0',

    'SVR Total.txt': '0',
    'SVR.txt': '0',
    'SVRC.txt': '0',
    'SVRD.txt': '0',
    'SVRTOR.txt': '0',

    'FFW Total.txt': '0',
    'FFW.txt': '0',
    'FFWC.txt': '0',
    'FFE.txt': '0',

    'TOA.txt': '0',
    'SVA.txt': '0',

    'SPS.txt': '0'
}

def close_program():
    os._exit(0)

def hide_to_system_tray():
    global icon
    image = Image.open('My_project.png')
    menu = (pystray.MenuItem("Exit", close_program),)
    icon = pystray.Icon("name", image, "My System Tray Icon", menu)
    icon.run()

def warning_count(data):
    # Initialize Counting Variables
    Alert_Total = 0
    Non_SPS_Total = 0

    TOR_total = 0
    TOR = 0
    TORR = 0
    TORP = 0
    TORE = 0

    SVR_total = 0
    SVR = 0
    SVRC = 0
    SVRD = 0
    SVRTOR = 0

    FFW_total = 0
    FFW = 0
    FFWC = 0
    FFE = 0

    TOA = 0
    SVA = 0

    SPS = 0

    for alert in data["features"]:
        properties = alert["properties"]
        event = properties["event"]

        # Damage Threat Parameters
        thunderstorm_damage_threat = properties.get("parameters", {}).get("thunderstormDamageThreat")
        tornado_damage_threat = properties.get("parameters", {}).get("tornadoDamageThreat")
        tornado_detection = properties.get("parameters", {}).get("tornadoDetection")
        flash_flood_damage_threat = properties.get("parameters", {}).get("flashFloodDamageThreat")

        # Alert Counting
        if event == 'Tornado Warning':
            Alert_Total += 1
            Non_SPS_Total += 1
            TOR_total += 1
            if tornado_detection == '["OBSERVED"]':
                TORR += 1
            if tornado_damage_threat == '["CONSIDERABLE"]':
                TORP += 1
            if tornado_damage_threat == '["CATASTROPHIC"]':
                TORE += 1
            else:
                TOR += 1
        
        if event == 'Severe Thunderstorm Warning':
            Alert_Total += 1
            Non_SPS_Total += 1
            SVR_total += 1
            if tornado_detection == '["POSSIBLE"]':
                SVRTOR += 1
            if thunderstorm_damage_threat == '["CONSIDERABLE"]':
                SVRC += 1
            if thunderstorm_damage_threat == '["DESTRUCTIVE"]':
                SVRD += 1
            else:
                SVR += 1
        
        if event == 'Flash Flood Warning':
            Alert_Total += 1
            Non_SPS_Total += 1
            FFW_total += 1
            if flash_flood_damage_threat == '["CONSIDERABLE"]':
                FFWC += 1
            if flash_flood_damage_threat == '["CATASTROPHIC"]':
                FFE += 1
            else:
                FFW += 1
        
        if event == 'Tornado Watch':
            Alert_Total += 1
            TOA += 1
        
        if event == 'Severe Thunderstorm Watch':
            Alert_Total += 1
            SVA += 1
        
        if event == 'Special Weather Statement':
            Alert_Total += 1
            SPS += 1

        
        # Previous Counts
        previous_Alert_Total_count = read_from_file(os.path.join("count", "Alert Total.txt"))
        previous_Non_SPS_Total_count = read_from_file(os.path.join("count", "Non SPS Total.txt"))

        previous_TOR_total_count = read_from_file(os.path.join("count", "TOR Total.txt"))
        previous_TOR_count = read_from_file(os.path.join("count", "TOR.txt"))
        previous_TORR_count = read_from_file(os.path.join("count", "TORR.txt"))
        previous_TORP_count = read_from_file(os.path.join("count", "TORP.txt"))
        previous_TORE_count = read_from_file(os.path.join("count", "TORE.txt"))

        previous_SVR_total_count = read_from_file(os.path.join("count", "SVR Total.txt"))
        previous_SVR_count = read_from_file(os.path.join("count", "SVR.txt"))
        previous_SVRC_count = read_from_file(os.path.join("count", "SVRC.txt"))
        previous_SVRD_count = read_from_file(os.path.join("count", "SVRD.txt"))
        previous_SVRTOR_count = read_from_file(os.path.join("count", "SVRTOR.txt"))

        previous_FFW_total_count = read_from_file(os.path.join("count", "FFW Total.txt"))
        previous_FFW_count = read_from_file(os.path.join("count", "FFW.txt"))
        previous_FFWC_count = read_from_file(os.path.join("count", "FFWC.txt"))
        previous_FFE_count = read_from_file(os.path.join("count", "FFE.txt"))

        previous_TOA_count = read_from_file(os.path.join("count", "TOA.txt"))
        previous_SVA_count = read_from_file(os.path.join("count", "SVA.txt"))

        previous_SPS_count = read_from_file(os.path.join("count", "SPS.txt"))

        # Update Count Files
        if Alert_Total != previous_Alert_Total_count:
            count_file_path = os.path.join('count', 'Alert Total.txt')
            write_to_file(count_file_path, str(Alert_Total))
            warnings_file_path = os.path.join('warnings', 'Alert Total.txt')
            write_to_file(warnings_file_path, f'Total Alerts: {Alert_Total}')
        
        if Non_SPS_Total != previous_Non_SPS_Total_count:
            count_file_path = os.path.join('count', 'Non SPS Total.txt')
            write_to_file(count_file_path, str(Non_SPS_Total))
            warnings_file_path = os.path.join('warnings', 'Non SPS Total.txt')
            write_to_file(warnings_file_path, f'Total Non-Special Weather Statements: {Non_SPS_Total}')

        if TOR_total != previous_TOR_total_count:
            count_file_path = os.path.join('count', 'TOR Total.txt')
            write_to_file(count_file_path, str(TOR_total))
            warnings_file_path = os.path.join('warnings', 'TOR Total.txt')
            write_to_file(warnings_file_path, f'Active Tornado Warnings: {TOR_total}')
        
        if TOR != previous_TOR_count:
            count_file_path = os.path.join('count', 'TOR.txt')
            write_to_file(count_file_path, str(TOR))
            warnings_file_path = os.path.join('warnings', 'TOR.txt')
            write_to_file(warnings_file_path, f'Tornado Warnings: {TOR}')
        
        if TORR != previous_TORR_count:
            count_file_path = os.path.join('count', 'TORR.txt')
            write_to_file(count_file_path, str(TORR))
            warnings_file_path = os.path.join('warnings', 'TORR.txt')
            write_to_file(warnings_file_path, f'Confirmed Tornado Warnings: {TORR}')
        
        if TORP != previous_TORP_count:
            count_file_path = os.path.join('count', 'TORP.txt')
            write_to_file(count_file_path, str(TORP))
            warnings_file_path = os.path.join('warnings', 'TORP.txt')
            write_to_file(warnings_file_path, f'PDS Tornado Warnings: {TORP}')
        
        if TORE != previous_TORE_count:
            count_file_path = os.path.join('count', 'TORE.txt')
            write_to_file(count_file_path, str(TORE))
            warnings_file_path = os.path.join('warnings', 'TORE.txt')
            write_to_file(warnings_file_path, f'Tornado Emergencies: {TORE}')
        

        if SVR_total != previous_SVR_total_count:
            count_file_path = os.path.join('count', 'SVR Total.txt')
            write_to_file(count_file_path, str(SVR_total))
            warnings_file_path = os.path.join('warnings', 'SVR Total.txt')
            write_to_file(warnings_file_path, f'Active Severe Thunderstorm Warnings: {SVR_total}')
        
        if SVR != previous_SVR_count:
            count_file_path = os.path.join('count', 'SVR.txt')
            write_to_file(count_file_path, str(SVR))
            warnings_file_path = os.path.join('warnings', 'SVR.txt')
            write_to_file(warnings_file_path, f'Severe Thunderstorm Warnings: {SVR}')
        
        if SVRC != previous_SVRC_count:
            count_file_path = os.path.join('count', 'SVRC.txt')
            write_to_file(count_file_path, str(SVRC))
            warnings_file_path = os.path.join('warnings', 'SVRC.txt')
            write_to_file(warnings_file_path, f'Considerable Severe Thunderstorm Warnings: {SVRC}')

        if SVRD != previous_SVRD_count:
            count_file_path = os.path.join('count', 'SVRD.txt')
            write_to_file(count_file_path, str(SVRD))
            warnings_file_path = os.path.join('warnings', 'SVRD.txt')
            write_to_file(warnings_file_path, f'Destructive Severe Thunderstorm Warnings: {SVRD}')
        
        if SVRTOR != previous_SVRTOR_count:
            count_file_path = os.path.join('count', 'SVRTOR.txt')
            write_to_file(count_file_path, str(SVRTOR))
            warnings_file_path = os.path.join('warnings', 'SVRTOR.txt')
            write_to_file(warnings_file_path, f'Severe Thunderstorm Emergencies: {SVRTOR}')
        

        if FFW_total != previous_FFW_total_count:
            count_file_path = os.path.join('count', 'FFW Total.txt')
            write_to_file(count_file_path, str(FFW_total))
            warnings_file_path = os.path.join('warnings', 'FFW Total.txt')
            write_to_file(warnings_file_path, f'Active Flash Flood Warnings: {FFW_total}')
        
        if FFW != previous_FFW_count:
            count_file_path = os.path.join('count', 'FFW.txt')
            write_to_file(count_file_path, str(FFW))
            warnings_file_path = os.path.join('warnings', 'FFW.txt')
            write_to_file(warnings_file_path, f'Flash Flood Warnings: {FFW}')
        
        if FFWC != previous_FFWC_count:
            count_file_path = os.path.join('count', 'FFWC.txt')
            write_to_file(count_file_path, str(FFWC))
            warnings_file_path = os.path.join('warnings', 'FFWC.txt')
            write_to_file(warnings_file_path, f'Considerable Flash Flood Warnings: {FFWC}')
        
        if FFE != previous_FFE_count:
            count_file_path = os.path.join('count', 'FFE.txt')
            write_to_file(count_file_path, str(FFE))
            warnings_file_path = os.path.join('warnings', 'FFE.txt')
            write_to_file(warnings_file_path, f'Flash Flood Emergencies: {FFE}')
        

        if TOA != previous_TOA_count:
            count_file_path = os.path.join('count', 'TOA.txt')
            write_to_file(count_file_path, str(TOA))
            warnings_file_path = os.path.join('warnings', 'TOA.txt')
            write_to_file(warnings_file_path, f'Tornado Watches: {TOA}')
        
        if SVA != previous_SVA_count:
            count_file_path = os.path.join('count', 'SVA.txt')
            write_to_file(count_file_path, str(SVA))
            warnings_file_path = os.path.join('warnings', 'SVA.txt')
            write_to_file(warnings_file_path, f'Severe Thunderstorm Watches: {SVA}')
        

        if SPS != previous_SPS_count:
            count_file_path = os.path.join('count', 'SPS.txt')
            write_to_file(count_file_path, str(SPS))
            warnings_file_path = os.path.join('warnings', 'SPS.txt')
            write_to_file(warnings_file_path, f'Seasonal Period Watches: {SPS}')
        
def write_to_file(filename, content):
    with open(filename, "w") as file:
        file.write(content + "\n")

def read_from_file(filename):
    try:
        with open(filename, "r") as file:
            content = file.read().strip()
            if content:
                cleaned_content = ''.join(char for char in content if char.isprintable())
                return int(cleaned_content)
            else:
                return 0
    except (FileNotFoundError, ValueError):
        return 0

def fetch_alerts():
    endpoint = "https://api.weather.gov/alerts/active"
    params = {
        "status": "actual",
        "message_type": "alert,update",
        "code": 'TOR,TOA,SVR,SVA,FFW,SVS,SPS',
        "region_type": "land",
        "urgency": "Immediate,Future,Expected",
        "severity": "Extreme,Severe,Moderate",
        "certainty": "Observed,Likely,Possible",
        "limit": 500
    }

    response = requests.get(endpoint, params=params)

    if response.status_code == 200:
        data = response.json()
        features = data["features"]

        warning_count(data)

        for alert in features:
            properties = alert["properties"]
            
            event = properties["event"]
            identifier = properties["id"]
            sent = properties["sent"]
            area_desc = properties["areaDesc"]
            expires = properties["expires"]

            sent_datetime = parser.parse(sent).astimezone(pytz.utc)
            expires_datetime = parser.parse(expires).astimezone(pytz.utc)

            if not database.alert_exists(identifier):
                # New Alert
                event, notification_message, area_desc, expires_datetime = alerts.process_alert(identifier, properties, sent_datetime, area_desc)
                display_alert(event, notification_message, area_desc)
                database.insert_alert(identifier, sent_datetime, expires_datetime, properties)
            else:
                # Alert Exists
                existing_alert = database.get_alert(identifier)
                existing_sent_datetime_str = existing_alert[1]
                existing_expires_datetime_str = existing_alert[2]
                existing_properties = existing_alert[3]

                existing_sent_datetime = parser.parse(existing_sent_datetime_str).replace(tzinfo=tz.tzutc())

                if sent_datetime != existing_sent_datetime:
                    # Update to Existing Alert
                    event, notification_message, area_desc, expires_datetime = alerts.process_alert(identifier, properties, sent_datetime, area_desc)
                    display_alert(event, notification_message, area_desc)
                    database.update_alert(identifier, sent_datetime, expires_datetime, properties)
    
    update_active_alerts()

def update_active_alerts_and_exit():
    update_active_alerts()

def display_alert(event, notification_message, area_desc):
    # Windows Notification
    notification.notify(
        title = event,
        message = notification_message,
        app_name = "Weather Alert",
        timeout = 10,
        toast = True
    )

    # Get Current Time
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    # Print Alert in Terminal
    print('')
    print(f'{current_time} - {notification_message}, {area_desc}')

system_tray_thread = threading.Thread(target=hide_to_system_tray)
system_tray_thread.start()

atexit.register(update_active_alerts_and_exit)

while True:
    fetch_alerts()
    time.sleep(5)