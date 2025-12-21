import random
from datetime import datetime, timedelta
import time
import json

def signal_generator(signal_id):
    #generate random value
    value = round(random.uniform(0, 100), 2)

    if(value > 90):
        status = "critical"
    elif(value>60):
        status = "high"
    else:
        status = "normal"
    
    signal = {
        "id": signal_id,
        "timestamp": datetime.now().isoformat(),
        "value": value,
        "status": status
    }
    return signal;

def generate_live_signals():
    print("Generating sample signal...")
    try:
        while True:
            data = signal_generator("Temperature")
            print(json.dumps(data, indent=2))
            time.sleep(1)

    except KeyboardInterrupt:
        print("Signal generation stopped.")

def generate_historical_signals(signal_id, start_time, end_time):
    historical_signals = []
    # i have to calculate weekly, daily, hourly, minutes averavge based on start and end time
    # if duration is greater than a year then weekly averages
    # if duration is greater than a week and less then a year then daily averages
    # if duration is greater than a day and less then a week then hourly averages
    # if duration is less than a day then minute averages
    duration = end_time - start_time
    if duration.days > 365:
        interval = 7 * 24 * 60 * 60  # weekly
    elif duration.days > 7:
        interval = 24 * 60 * 60  # daily
    elif duration.days > 1:
        interval = 60 * 60  # hourly
    else:
        interval = 60  # minutely

    current_time = start_time
    while current_time < end_time:
        signal = signal_generator(signal_id)
        signal["timestamp"] = current_time.isoformat()
        historical_signals.append(signal)
        current_time += timedelta(seconds=interval)
    
    return historical_signals

if __name__ == "__main__":
    hist_data = generate_historical_signals("Temprature", datetime.now() - timedelta(days=2), datetime.now())
    print("Historical Signals:")
    print(hist_data.__len__())
    liv_data = generate_live_signals()
    print("Live Signals:")
    print(liv_data)