import random
import time
from datetime import datetime, timedelta


def signal_generator(signal_id):
    """Generate a single signal reading with status"""
    value = round(random.uniform(0, 100), 2)

    if value > 90:
        status = "critical"
    elif value > 60:
        status = "high"
    else:
        status = "normal"
    
    signal = {
        "id": signal_id,
        "timestamp": datetime.now().isoformat(),
        "value": value,
        "status": status
    }
    return signal


def generate_live_signals():
    """Generate live signal stream"""
    print("Generating sample signal...")
    try:
        while True:
            data = signal_generator("Temperature")
            print(data)
            time.sleep(1)
    except KeyboardInterrupt as e:
        print("Signal generation stopped.")
        raise e


def calculate_average_value(base_value=50, variance=15):
    """Generate a realistic value based on a base with variance"""
    return round(random.gauss(base_value, variance), 2)


def get_aggregation_level(duration):
    """Determine the appropriate aggregation level based on time duration
    
    Returns: (interval_seconds, level_name, samples_per_interval)
    - Year+: Weekly averages (7 sample readings per week)
    - Week+: Daily averages (6 sample readings per day)
    - Day+: Hourly averages (4 sample readings per hour)
    - <Day: Minute averages (1-2 readings per minute)
    """
    if duration.days > 365:
        return 7 * 24 * 60 * 60, "weekly", 7
    if duration.days > 7:
        return 24 * 60 * 60, "daily", 6
    if duration.days > 1:
        return 60 * 60, "hourly", 4
    return 60, "minutely", 2


def generate_historical_signals(signal_id, start_time, end_time):
    """Generate historical signal data with Level-of-Detail (LOD) aggregation
    
    Adapts the granularity and averaging based on the time range:
    - Year range: Weekly aggregates
    - Month range: Daily aggregates
    - Week range: Hourly aggregates
    - Day range: Minute-level data
    
    Each aggregate is calculated as the average of multiple sample readings
    within that period, providing realistic data visualization at any scale.
    """
    # Base values vary by signal type for realistic data
    signal_base_values = {
        "Temperature": 20,      # Celsius
        "Humidity": 60,         # Percentage
        "Pressure": 1013,       # hPa
        "Power": 500,           # Watts
        "Flow": 100,            # L/min
    }
    
    historical_signals = []
    duration = end_time - start_time
    interval_seconds, level_name, samples_per_interval = get_aggregation_level(duration)
    
    base_value = signal_base_values.get(
        signal_id.split('_')[0] if '_' in signal_id else signal_id,
        50
    )
    
    current_time = start_time
    while current_time < end_time:
        # Generate multiple samples within this interval and average them
        sample_values = []
        sample_statuses = []
        
        for _ in range(samples_per_interval):
            sample_value = calculate_average_value(base_value, variance=10)
            # Ensure value is within realistic bounds (0-100 for most signals)
            sample_value = max(0, min(100, sample_value))
            sample_values.append(sample_value)
            
            # Determine status based on sample value
            if sample_value > 90:
                sample_statuses.append("critical")
            elif sample_value > 60:
                sample_statuses.append("high")
            else:
                sample_statuses.append("normal")
        
        # Calculate aggregate (average of samples)
        avg_value = round(sum(sample_values) / len(sample_values), 2)
        
        # Determine status based on average
        critical_count = sample_statuses.count("critical")
        high_count = sample_statuses.count("high")
        
        # Status thresholds: 30% of samples in a category
        critical_threshold = samples_per_interval * 0.3
        high_threshold = samples_per_interval * 0.3
        
        if critical_count > critical_threshold:
            status = "critical"
        elif high_count > high_threshold:
            status = "high"
        else:
            status = "normal"
        
        signal = {
            "id": signal_id,
            "timestamp": current_time.isoformat(),
            "value": avg_value,
            "status": status,
            "aggregation_level": level_name,
            "sample_count": samples_per_interval,
            "min_value": round(min(sample_values), 2),
            "max_value": round(max(sample_values), 2)
        }
        historical_signals.append(signal)
        current_time += timedelta(seconds=interval_seconds)
    
    return historical_signals


if __name__ == "__main__":
    hist_data = generate_historical_signals(
        "Temperature",
        datetime.now() - timedelta(days=2),
        datetime.now()
    )
    print("Historical Signals:")
    print(len(hist_data))