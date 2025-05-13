def check_temperature_alert(temp, room, patient_id):
    if temp < 10.0 or temp > 30.0:
        return f"[ALERT]  {patient_id}: Temperature in {room} is {temp}°C"
    return None

def check_humidity_alert(humidity, room, patient_id):
    if humidity < 40.0 or humidity > 60.0:
        return f"[ALERT]  {patient_id}: Humidity in {room} is {humidity}%"
    return None

def check_device_duration_alert(appliance, duration, room, patient_id):
    if duration > 30:
        return f"[ALERT]  {patient_id}: {appliance} in {room} has been ON for {duration} minutes"
    return None
