import pandas as pd
import numpy as np
from fitparse import FitFile
import folium

def import_data_fit(filename:str) -> pd.DataFrame:
    '''
    Function to transform a FIT file in to a dataframe

    Input : Filename or filepath (here data.fit in our case)
    Output : two dataframe, one with datas and the other one with the units
    '''
    fitfile = FitFile(filename)
    # 2 lists to create the dataframe
    records = []
    units = []
    # loop on each record
    for record in fitfile.get_messages("record"):
        # Data and unit dictionnary
        data = {field.name:field.value for field in record}
        unit = {field.name: field.units for field in record}
        # Append to the list
        records.append(data)
        units.append(unit)

    # Creation of the dataframe
    df_data = pd.DataFrame(records)
    df_unit = pd.DataFrame(units)
    # Series to dataframe if needed
    if isinstance(df_data, pd.Series):
        df_data = pd.DataFrame([df_data])
    if isinstance(df_unit, pd.Series):
        df_unit = pd.DataFrame([df_unit])

    return df_data, df_unit

def mapping_session(df : pd.DataFrame, latitude:str, longitude:str):
    '''
    Function that allow us to map the session thanks to GPS points

    Inputs : 
    - Dataframe of datas
    - String of latitude column
    - String of longitude column

    Output : 
    - m, a folium object corresponding to the map
    '''

    # Focus on start point session
    start_lat = df.iloc[0][latitude]
    start_long = df.iloc[0][longitude]
    m = folium.Map(location=[start_lat, start_long], zoom_start=15)

    # Show the route
    folium.PolyLine(
        locations=df[[latitude, longitude]].values.tolist(),
        color="blue",
        weight=3,
        opacity=0.8
    ).add_to(m)

    # Start and finish point
    folium.Marker(
        [start_lat, start_long],
        popup="Start",
        icon=folium.Icon(color="green")
    ).add_to(m)
    # End point
    end_lat = df.iloc[-1][latitude]
    end_long = df.iloc[-1][longitude]
    # Marker
    folium.Marker(
        [end_lat, end_long],
        popup="Finish",
        icon=folium.Icon(color="red")
    ).add_to(m)
    return m

def get_hr_zone(hr, max_hr):
    '''
    This function creates heart rate zones

    Inputs :
    - hr : the heart rate value in the dataframe
    - max_hr : maximum heart rate

    Output : 
    - zone corresponding to the heart rate
    '''
    if hr<0.6*max_hr:
        return "zone_1"
    elif hr<0.7*max_hr:
        return "zone_2"
    elif hr<0.8*max_hr:
        return "zone_3"
    elif hr<0.9*max_hr:
        return "zone_4"
    else:
        return "zone_5"

def format_minutes(x):
    mins = int(x)
    secs = int((x - mins) * 60)
    return f"{mins:02d}:{secs:02d}"

def format_bin_left(b):
    minutes = int(b.left // 60)
    seconds = int(b.left % 60)
    return f"{minutes}:{seconds:02d}"

def all_session_stat(df : pd.DataFrame):
    '''
    This function creates a dataframe with some statistics such as total distance, 
    running time, maximum, minimum and the average heart rate, maximum, minimum and the average altitude,
    the elevetion gain and loss, the average and maximum speed, the pace and the average temperature.

    Input : df :Dataframe of datas

    Output : df_stats : a dataframe with statistics
    '''
    stats = {}
    # Total distance (value of the last row)
    stats['Total_distance_km'] = round(float(df['distance'].iloc[-1])/1000, 2)
    # Running time (difference between the last and the first timestamp)
    stats['Running_time'] = str(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).split( )[2]
    # Maximum, minimum and average heart rate
    stats['Max_hr_bpm'] = int(df['heart_rate'].max())
    stats['Min_hr_bpm'] = int(df['heart_rate'].min())
    stats['Average_hr_bpm'] = int(df['heart_rate'].mean())
    # Maximum, minimum and average altitude
    stats['Max_altitude_m'] = int(df['altitude'].max())
    stats['Min_altitude_m'] = int(df['altitude'].min())
    stats['Average_altitude_m'] = int(df['altitude'].mean())
    # Elevation gain and loss
    # Difference between two consecutive altitude values
    altitude_diff = df['altitude'].diff()
    stats['Elevation_gain_m'] = round(float(altitude_diff[altitude_diff > 0].sum()),2)
    stats['Elevation_loss_m'] = round(float(altitude_diff[altitude_diff < 0].sum()),2)
    # Average and maximum speed
    stats['Average_enhanced_speed_m/s'] = round(float(df['enhanced_speed'].mean()),2)
    stats['Average_enhanced_speed_km/h'] = round(float(df['enhanced_speed'].mean()*3.6),2)
    stats['Max_enhanced_speed_m/s'] = round(float(df['enhanced_speed'].max()),2)
    stats['Max_enhanced_speed_km/h'] = round(float(df['enhanced_speed'].max()*3.6),2)
    stats['Average_speed_m/s'] = round(float(df['speed'].mean()),2)
    # Pace (min/km)
    stats['Pace_min/km'] = round(1000 / (stats['Average_enhanced_speed_m/s'] * 60),2)
    stats['Average_temperature'] = round(float(df['temperature'].mean()),2)
    # Dico to dataframe
    df_stats = pd.DataFrame(stats.items(), columns=["Metric", "Value"])
    return df_stats

def running_session_stats(df_warmup: pd.DataFrame, df_speed_interval: pd.DataFrame, df_cooldown: pd.DataFrame):
    '''
    Function that creates three dataframes with statistics of each session part

    Input : Dataframe of datas
    Outputs : Three dataframes
    '''
    # Dico with all the intervals
    df_zone = {'Warmup' : df_warmup, 'Speed_interval' : df_speed_interval, 'Cooldown' : df_cooldown}
    # Dico to stock results
    dico_interval={}
    # Loop on each dataframe
    for name, df in df_zone.items():
        dico_interval[f'Total_distance_km_{name}'] = round(float(df['distance'].iloc[-1] - df['distance'].iloc[0])/1000, 2)
        dico_interval[f'Running_time_{name}'] = str(df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).split( )[2]
        dico_interval[f'Max_hr__bpm_{name}'] = int(df['heart_rate'].max())
        dico_interval[f'Min_hr_bpm_{name}'] = int(df['heart_rate'].min())
        dico_interval[f'Average_hr_bpm_{name}'] = int(df['heart_rate'].mean())
        dico_interval[f'Max_altitude_m_{name}'] = int(df['altitude'].max())
        dico_interval[f'Min_altitude_m_{name}'] = int(df['altitude'].min())
        dico_interval[f'Average_altitude_m_{name}'] = int(df['altitude'].mean())
        altitude_diff = df['altitude'].diff()
        dico_interval[f'Elevation_gain_m_{name}'] = round(float(altitude_diff[altitude_diff > 0].sum()),2)
        dico_interval[f'Elevation_loss_m_{name}'] = round(float(altitude_diff[altitude_diff < 0].sum()),2)
        dico_interval[f'Average_enhanced_speed_m/s_{name}'] = round(float(df['enhanced_speed'].mean()),2)
        dico_interval[f'Average_enhanced_speed_km/h_{name}'] = round(float(df['enhanced_speed'].mean()*3.6),2)
        dico_interval[f'Max_enhanced_speed_m/s_{name}'] = round(float(df['enhanced_speed'].max()),2)
        dico_interval[f'Max_enhanced_speed_km/h_{name}'] = round(float(df['enhanced_speed'].max()*3.6),2)
        dico_interval[f'Average_speed_m/s_{name}'] = round(float(df['speed'].mean()),2)
        dico_interval[f'Pace_min/km_{name}'] = round(1000 / (dico_interval[f'Average_enhanced_speed_m/s_{name}'] * 60),2)

    dico_warmup = {}
    dico_speed = {}
    dico_cooldown = {}

    # condtion on the last character of the word (key dictionnary)
    for key, value in dico_interval.items():
        if str(key)[-1] == "p":
            dico_warmup[key] = value
        elif str(key)[-1] == "l":
            dico_speed[key]=value
        elif str(key)[-1]=="n":
            dico_cooldown[key]=value

    # Creation of dataframes
    df_warmup_stat = pd.DataFrame(dico_warmup.items(), columns=["Metric", "Value"])
    df_speed_stat = pd.DataFrame(dico_speed.items(), columns=["Metric", "Value"])
    df_cooldown_stat = pd.DataFrame(dico_cooldown.items(), columns=["Metric", "Value"])
    return df_warmup_stat, df_speed_stat, df_cooldown_stat

def speed_session_stat(df_speed_interval: pd.DataFrame, threshold : float):
    '''
    Function that creates a dataframe with statistics of the speed interval session part

    Input : Dataframe of datas and a threshold to define the speed intervals
    Outputs : 
    - df_intervals_speed : statistics of the speed intervals
    - df_intervals_rest : statistics of the rest intervals
    '''
    # Keep only relevant datas ie enhanced_speed > threshold
    df_speed_interval['is_effort'] = df_speed_interval['enhanced_speed']> threshold
    # New column to identify blocks
    df_speed_interval['change'] = df_speed_interval['is_effort'].ne(df_speed_interval['is_effort'].shift())
    # Cumulative sum to identify blocks
    df_speed_interval['block'] = df_speed_interval['change'].cumsum()
    intervals_speed = []

    # effort block analysis
    for _, group in df_speed_interval.groupby('block'):
        # effort block
        if group['is_effort'].iloc[0]: 
            # first row and last row of the block
            start_time = group['time'].iloc[0]
            end_time = group['time'].iloc[-1]
            duration = end_time - start_time
            # Statistics
            avg_speed = group['enhanced_speed'].mean()
            max_speed = group['enhanced_speed'].max()
            avg_hr = group['heart_rate'].mean()
            max_hr = group['heart_rate'].max()
            avg_pace = 1000 / (group['enhanced_speed']*60).mean()
            # Append to the list
            intervals_speed.append({
                'Start_time (min)': start_time,
                'End_time (min)': end_time,
                'Duration (min)': duration,
                'Average_speed (m/s)': round(avg_speed,2),
                'Max_speed (m/s)': round(max_speed,2),
                'Average_HR (bpm)': round(avg_hr,2),
                'Max_HR (bpm)': max_hr,
                'Average_pace (min/km)': round(avg_pace,2)
            })
    # Dico to dataframe
    df_intervals_speed = pd.DataFrame(intervals_speed)

    # rest block analysis
    rests=[]
    # Loop on the length of the dataframe
    for i in range(len(df_intervals_speed)-1):
        # Rest start and end + duration
        rest_start = df_intervals_speed['End_time (min)'].iloc[i]
        rest_end = df_intervals_speed['Start_time (min)'].iloc[i+1]
        rest_duration = rest_end - rest_start
        
        # Average speed of rest 
        avg_speed = df_speed_interval[(df_speed_interval['time'] >= rest_start) & (df_speed_interval['time'] <= rest_end)]['enhanced_speed'].mean()
        # Average heart rate of rest
        avg_hr = df_speed_interval[(df_speed_interval['time'] >= rest_start) & (df_speed_interval['time'] <= rest_end)]['heart_rate'].mean()
        # Average pace of rest
        avg_pace = (1000 / df_speed_interval[(df_speed_interval['time'] >= rest_start) & (df_speed_interval['time'] <= rest_end)]['enhanced_speed'] * 60).mean()
        # Append to the list
        rests.append({
            'Rest_start (min)': rest_start,
            'Rest_end (min)': rest_end,
            'Rest_duration (min)': rest_duration,
            'Average_rest_HR (bpm)': round(avg_hr,2)
        })
    # Dico to dataframe
    df_intervals_rest = pd.DataFrame(rests)

    # Minute formating
    df_intervals_speed['Start_time (min)'] = df_intervals_speed['Start_time (min)'].apply(format_minutes)
    df_intervals_speed['End_time (min)'] = df_intervals_speed['End_time (min)'].apply(format_minutes)
    df_intervals_speed['Duration (min)'] = df_intervals_speed['Duration (min)'].apply(format_minutes)

    df_intervals_rest['Rest_start (min)'] = df_intervals_rest['Rest_start (min)'].apply(format_minutes)
    df_intervals_rest['Rest_end (min)'] = df_intervals_rest['Rest_end (min)'].apply(format_minutes)
    df_intervals_rest['Rest_duration (min)'] = df_intervals_rest['Rest_duration (min)'].apply(format_minutes)
    return df_intervals_speed, df_intervals_rest

def pace(df:pd.DataFrame):
    '''
    Function that creates a dataframe with pace bins and the time spent in each bin

    Input : Dataframe of datas
    Output : a dataframe
    '''
    df_pace = df[df['enhanced_speed']>0].copy()
    df_pace['Pace_min_km'] = 1000 / (df_pace['enhanced_speed'] * 60)
    df_pace['Pace_s_km'] = df_pace['Pace_min_km']*60
    # Create bins of 10s from 150s to max of pace or 410s
    bins = np.arange(150, min(np.max(df_pace['Pace_s_km']), 410), 10)
    # Cuting by bins
    df_pace['pace_zone'] = pd.cut(df_pace['Pace_s_km'], bins=bins)
    # Time spent in each bin
    time_per_zone = df_pace.groupby('pace_zone')['delta_time'].sum().dropna()
    time_per_zone_min = time_per_zone / 60
    # Formatting the x labels
    x_labels = [format_bin_left(b) for b in time_per_zone_min.index]
    return x_labels, time_per_zone_min