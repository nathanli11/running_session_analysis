# Librairies import
import functions as fc
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

# Streamlit configuration
st.set_page_config(
    page_title="Running Analysis",
    layout="wide",  
    initial_sidebar_state="expanded"
)

### Data filter and preparation
df_data, df_unit = fc.import_data_fit("data.fit")
# Unit recuperation
df_unit = df_unit.iloc[0]

# Sort values by timestamp
df_data = df_data.sort_values('timestamp')
# New column dela_time corresponding of the time between two rows of timestamp column
df_data['delta_time'] = df_data['timestamp'].diff().dt.total_seconds()
# Organization of the dataframe
cols = ['timestamp'] + [col for col in df_data.columns if col != 'timestamp']
df_data = df_data[cols]

# Divide by 60 to have minute data units
df_data['time'] = (df_data['timestamp'] - df_data['timestamp'].iloc[0]).dt.total_seconds()/60
df_data.drop(columns=['unknown_87', 'unknown_88','unknown_90'], inplace=True)
# Maximum of heart rate + 5%
hr_max = df_data['heart_rate'].max()*1.05 # It is a choice to add 5% of the max heart rate of the session to determine the max heart rate of the runner
df_data['heart_rate_zone'] = df_data['heart_rate'].apply(lambda hr: fc.get_hr_zone(hr, hr_max))

### Running session mapping
df_data['position_lat'] = df_data['position_lat']*(180/2**31)
df_data['position_long'] = df_data['position_long']*(180/2**31)
m = fc.mapping_session(df_data, "position_lat", "position_long")

### Running session stats
df_stats = fc.all_session_stat(df_data)


# Title of streamlit app
st.title("Analysis of the track runnning session")
# Cut the page into two columns
col1, col2 = st.columns([1,2])
# Streamlit mapping session 
with col1:
    st.subheader("Session Mapping")
    # Folium map
    st_folium(m, width=600, height=400)

# Streamlit stats
with col2:
    st.subheader("Training statistics")
    # Display dataframe
    st.dataframe(df_stats, hide_index=True)
# Comments
st.markdown("As we can observe, the running session took place around an athletics stadium in Nîmes. " \
    "The training location may raise questions about the temperature during the training and during the race. " \
    "Moreover, we can study some statistics such as the total distance, the running time or the heart rate.")

# Entire session
st.subheader("Activity plot")
# Mask for running and walking
running_mask = df_data['activity_type'] == 'running'
walking_mask = df_data['activity_type'] == 'walking'
# Creation of the plotly figure
fig = go.Figure()
# Scatter plot of enhanced speed
fig.add_trace(go.Scatter(
    x = df_data['time'],
    y=df_data['enhanced_speed'],
    mode='lines',
    name='Speed (m/s)',
    line=dict(color='black', width=2)
))
# Add areas for running
fig.add_trace(go.Scatter(
    x=df_data['time'],
    y=df_data['enhanced_speed'],
    mode='none',
    name='Running',
    fill='tozeroy',
    fillcolor='rgba(255,0,0,0.1)',
    hoverinfo='skip'
))
# Add areas for walking 
fig.add_trace(go.Scatter(
    x=df_data['time'],
    y=df_data['enhanced_speed'].where(walking_mask, 0),
    mode='none',
    fill='tozeroy',
    fillcolor='rgba(0,0,255,1)',
    name='Walking',
    hoverinfo='skip'
))
# Layout 
fig.update_layout(
    title="Enhanced speed with running segments",
    xaxis_title="Time",
    yaxis_title="Enhanced speed",
    legend=dict(yanchor="top",y=0.99, xanchor="left",x=0.01),
    width=1200,
    height=600
)
# streamlit plot figure
st.plotly_chart(fig, use_container_width=True)
# Comments
st.markdown("This session is divided into three parts : warm-up, speed intervals and cool-down. " \
"In the speed interval zone, we can see some walking zones probably corresponding to rest periods. " \
"In addition, we also see gaps in activity that may correspond to break zones when the watch turns off.")

# Session parts
# End of warm-up corresponding to the first time after break of more than 80s
end_warmup = df_data.index[df_data['delta_time']>80][0]
# Creation of warm-up dataframe 
df_warmup = df_data.iloc[:end_warmup]
# Start of speed interval corresponding to the first row after the end of warm-up
start_speed_interval = df_warmup.index[-1]+1
# End of speed interval corresponding to the second time after break of more than 80s
end_speed_interval = df_data.index[df_data['delta_time']>80][1]
# Creation of speed interval dataframe
df_speed_interval = df_data.iloc[start_speed_interval:end_speed_interval]
# Start of cool-down corresponding to the first row after the end of speed interval
start_cool_down = df_speed_interval.index[-1]+1
# Creation of cool-down dataframe (start_cool_down to the end)
df_cooldown = df_data.iloc[start_cool_down:]

# Stats per part of the running session
df_warmup_stat, df_speed_stat, df_cooldown_stat = fc.running_session_stats(df_warmup, df_speed_interval, df_cooldown)

# Streamlit display
st.subheader("Interval statistics")
# Cut the page into three columns
col1, col2, col3 = st.columns(3)
# Display dataframe warm-up on first column
with col1:
    st.subheader("Warm-up statistics")
    st.dataframe(df_warmup_stat, hide_index=True)
# Display dataframe speed interval on second column
with col2:
    st.subheader("Speed interval statistics")
    st.dataframe(df_speed_stat, hide_index=True)
# Display dataframe cool-down on third column
with col3:
    st.subheader("Cool-down statistics")
    st.dataframe(df_cooldown_stat, hide_index=True)

# Plot some graphs
fig = make_subplots(specs=[[{"secondary_y": True}]])

#---- WARM UP -----
# Create a scatter plot with the speed and the heart rate
# 1 : Speed 
fig.add_trace(go.Scatter(
    x=df_warmup['time'],
    y=df_warmup['enhanced_speed'],
    mode='lines',
    name='Speed (m/s)',
    line=dict(color='black', width=2),
    visible=True
), secondary_y=False)
# 2 : HR
fig.add_trace(go.Scatter(
    x=df_warmup['time'],
    y=df_warmup['heart_rate'],
    mode='lines',
    name='Heart Rate (bpm)',
    line=dict(color='blue', width=2),
    visible=True
), secondary_y=True)
fig.update_layout(
    title=dict(
        text="Speed (m/s) and heart rate over time",
        x=0.5,
        xanchor='center'
    ),
    xaxis_title="Time",
    yaxis_title="Speed (m/s)",
    width=1200,
    height=600)
# streamlit subheader and plot
st.subheader('Warm-up visualization')
st.plotly_chart(fig, use_container_width=True)

st.markdown("This is the warm-up phase. Speed gradually increases over approximately 25 minutes to an average " \
"speed of 2,97 m/s (10,69 km/h). We also notice an increase in heart rate at the beginning of the session, from around " \
"130 bpm to around 150 bpm. It may be useful to add a few gradual accelerations to increase " \
"the heart rate in order to prepare for the speed interval session.")


# ------ Speed intervals -----
st.subheader("Speed intervals")
st.markdown("The speed interval session consists of 30 seconds of effort followed by 50 seconds of rest. The " \
"total distance is 5,45 km at an average speed of 3,73 m/s. This session is divided into 10 speed intervals, then a " \
"break and then again 8 speed intervals.")

# Speed interval datas and stats
threshold = 4.0 # 4 is chosen by me. It is the point where rest speed < 4 and effort speed > 4
df_intervals_speed, df_intervals_rest = fc.speed_session_stat(df_speed_interval, threshold)

# streamlit for display dataframes
col4, col5 = st.columns(2)
with col4:
    st.dataframe(df_intervals_speed, hide_index=True, width=800, height=300)
    st.markdown("The effort session shows us that for the first 10 intervals, the pace tends to increase. In other words, "\
                "you run faster at the end of the intervals. Your heart rate also increases. " \
    "The second part of the speed session, which took place after the break, is faster than the first. The heart rate " \
    "is also higher than in the first part, but this is due to the speed. In fact, when we look at the two " \
    "parts, we see that at the same speed, the heart is very similar." \
    "\n" \
    "This does not indicate particular fatigue, but rather intense effort over 30 seconds.")
with col5:
    st.dataframe(df_intervals_rest, hide_index=True, width=500, height=300)
    st.markdown("The rest phases provide important informations. The rest time between two efforts is approximately " \
                "50 seconds. We note that the heart rate drops appropriately between the two efforts. " \
                "However, we observe that it does not drop as much as the end as at the beginning, going from 125 bpm " \
                "to 169 bpm. This indicates fatigue, but it is completely normal. \n" \
                "This fatigue is particularly noticeable in the second block of training. Unlike the first block, where " \
                "the heart rate dropped to around 166 bpm at the end, in this second part we see that it remains above 170 bpm.")

# Pace visualization
x_labels, time_per_zone_min = fc.pace(df_speed_interval)
# Bar plot for pace visualization
fig3 = px.bar(
    x = x_labels,
    y=time_per_zone_min.values,
    labels={'x':'Pace (min/km)', 'y': 'Time (min)'},
    title="Time spent in each pace zone"
    )
fig3.update_layout(
    xaxis=dict(tickangle=-45),
    width=800,
    height=500,
    title=dict(x=0.5)
    )
# Plot
st.plotly_chart(fig3, use_container_width=True)
st.markdown("We note that most of the time, speed intervals are between 2:40 and 3 min/km." \
            "These are speeds that cause fatigue. Indeed, the heart rate is very high during these intervals. " \
            "However, we can see that you are capable of running at a pace of 2:40 min/km almost during 3min and at 2:50 min/km during 4min15s, which is very good. " )

# Graph : speed and cadence
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
# 1 - speed : scatter plot
fig1.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['enhanced_speed'],
    mode='lines',
    name='Speed (m/s)',
    line=dict(color='black', width=2), 
    visible = True
), secondary_y=False)
# 2 - cadence : bar plot
fig1.add_trace(go.Bar(
    x=df_speed_interval['time'],
    y=df_speed_interval['cadence'],
    name='Cadence (rpm)',
    marker=dict(color='blue'),
    opacity=0.5
), secondary_y=True)
fig1.update_layout(
    title=dict(text="Speed and Cadence", x=0.5, xanchor='center'),
    xaxis_title="Time",
    yaxis_title="Speed (m/s)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    width=600,
    height=500
)
fig1.update_yaxes(title_text="Cadence (ppm)", secondary_y=True)
# Graph : speed and step length
fig2 = make_subplots(specs=[[{"secondary_y": True}]])
# 1 - speed : scatter plot
fig2.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['enhanced_speed'],
    mode='lines',
    name='Speed (m/s)',
    line=dict(color='black', width=2),
    visible=True
), secondary_y=False)
# 2 - Step length : bar plot
fig2.add_trace(go.Bar(
    x=df_speed_interval['time'],
    y=df_speed_interval['step_length']/10,
    name='Step length (cm)',
    marker=dict(color='green'),
    opacity=0.5
), secondary_y=True)
# Layout
fig2.update_layout(
    title=dict(text="Speed & Step length", x=0.5, xanchor='center'),
    xaxis_title="Time",
    yaxis_title="Speed (m/s)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    width=600,
    height=500
)
fig2.update_yaxes(title_text="Step length (cm)", secondary_y=True)

# Comments
col6, col7 = st.columns(2)
with col6:
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("The first graph clearly shows the correlation between speed and cadence, as well as between speed and step legth on the second one. " \
    "\n" \
    "We can see that as speed increases, cadence also increases. This is perfectly natural. We can see that cadence does not decrease as the session progresses, which is a good thing ! " \
    "This means that fatigue is not signficant. \n" \
    "The cadence even exceeds 200 ppm at times. A high cadence means less time in contact with the ground, which limits impact forces. You maintain your technique and efficiency even when fatigued." \
    "\n")
with col7:
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("The conclusions are broadly the same for step length. It increases with speed. " \
    "However, we can see signs of fatigue in the increase in step length at the end of the interval, " \
    "particularly in the last 5 strides. \n \n")
# Graph : stance time and speed
fig1 = go.Figure()
# Scatter plot
fig1.add_trace(go.Scatter(
    x = df_speed_interval['time'],
    y=df_speed_interval['stance_time']/100,
    mode='lines',
    name='Stance Time (ms * 10e-2)',
    line=dict(color='blue', width=2)
))
# Scatter plot
fig1.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['enhanced_speed'],
    mode='none',
    name='Speed (m/s)',
    fill='tozeroy',
    fillcolor='rgba(255,0,0,0.1)',
    hoverinfo='skip'
))
fig1.update_layout(
    title="Stance Time over time",
    xaxis_title="Time",
    yaxis_title="Stance Time (ms * 10e-2)",
    legend=dict(yanchor="top",y=0.99, xanchor="left",x=0.01),
    width=1000,
    height=500
)

st.subheader(" Stance Time and Vertical oscillation & Vertical ratio")
# Graph: vertical oscillation and vertical ratio and speed
fig2 = make_subplots(specs=[[{"secondary_y": True}]])
fig2.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['vertical_oscillation'],
    mode='lines',
    name='Vertical Oscillation (mm)',
    line=dict(color='black', width=2)
), secondary_y=True)
fig2.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['vertical_ratio'],
    mode='lines',
    name='Vertical ratio (%)',
    line=dict(color='green', width=2, dash='dot')
), secondary_y=True)
fig2.add_trace(go.Scatter(
    x=df_speed_interval['time'],
    y=df_speed_interval['enhanced_speed'],
    mode='none',
    name='Speed (m/s)',
    fill='tozeroy',
    fillcolor='rgba(255,0,0,0.1)',
    hoverinfo='skip'
), secondary_y=False)
fig2.update_layout(
    title=dict(text="Vitesse vs Oscillation verticale & Vertical ratio"),
    xaxis_title="Time (min)",
    yaxis_title="Speed (m/s)",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    width=1000,
    height=500
)
fig2.update_yaxes(title_text="Oscillation (mm) / Vertical ratio (%)", secondary_y=True)
# plot and comments
col8, col9 = st.columns(2)
with col8:
    st.plotly_chart(fig1, use_container_width=True)
    st.markdown("Stance time decreases as speed increases, which is to be expected. However, we note that at similar " \
    "speeds, stance time varies from one interval to another. For example, between 45 and 50 min, stance time is fairly low and consistent (2*10e-2 - 3*10e-2 ms). " \
    "Between 55 and 65 min, at equivalent speed, stance time is slightly higher, around 3*10e-10. This reflects muscle fatigue : the stride loses tone.")
with col9:
    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("Vertical oscillation averages around 4-6 mm. We note efficient strides. You use less energy when rebounding. " \
    "The vertical ratio remains low and stable. The lower the ratio, the more energy is directed forward. " \
    "We do not see any major deviation in the ratio during training. Even when fatigued, you maintain good propulsion mechanics.")

# Heart rate analysis
st.subheader("Heart Rate zones and analysis")
# Groupby heart rate zone to have the length of time in each zone
time_per_zone_hr = df_speed_interval.groupby('heart_rate_zone')['delta_time'].sum().sort_index()
# second to minute
time_per_zone_hr_min = time_per_zone_hr / 60  

df_zone_plot = time_per_zone_hr_min.reset_index()
df_zone_plot.columns = ['Heart Rate Zone', 'Time (min)']
# Plot Heart Rate Zones
# Bar plot with horizontal orientation
fig4 = px.bar(
    df_zone_plot,
    x='Time (min)',
    y='Heart Rate Zone',
    orientation='h',
    color='Time (min)',
    color_continuous_scale='Viridis',
    text='Time (min)',
    title="Time spent in each heart rate zone"
)
# Text on the bar plot
fig4.update_traces(
    texttemplate='%{text:.1f} min',
    textposition='inside',
    marker_line_color='black',
    marker_line_width=1
)
fig4.update_layout(
    coloraxis_showscale=False,
    yaxis=dict(autorange="reversed"), 
    xaxis_title="Time (minutes)",
    yaxis_title="Heart Rate Zone",
    width=800,
    height=500,
    title=dict(x=0.5)
)
st.plotly_chart(fig4, use_container_width=True)
st.markdown("During the speed intervals, you spent more time in high heart rate zones (zone 4 and zone 5). Zone 4 corresponds to 80-90% of your maximum heart rate, while zone 5 is " \
"above 90%. \n" \
"This is perfectly normal for this type of training, which aims to improve your VO2 max and your ability to sustain high intensity efforts. \n"
"You spend 13,7 min in zone 4 and 5,7 min in zone 5. This is a good balance, allowing you to work on your endurance and speed without overloading your cardiovascular system. " \
"Compared to a trail run, it is important go spend time in high zone because during the climbs, your heart rate will increase significantly. " \
"It is therefore important to be accustomed to these high heart rates.\
\n" \
"However, it is also important to monitor your recovery during the rest periods. You spend 14,7 min in zone 1 and 1,5 min in zone 2. " \
"This allow your heart to go down rapidly and to rest between your working intervals. ")

# Cardiac drift
st.subheader("Cardiac drift scatter plot")
# scatter plot
fig = px.scatter(
    df_speed_interval,
    x='enhanced_speed',
    y='heart_rate',
    color='time',
    color_continuous_scale='Viridis',
    labels={
        'enhanced_speed': 'Speed (m/s)',
        'heart_rate': 'Heart Rate (bpm)',
        'time': 'Time (min)'
    },
    title="Speed vs Heart Rate with temporal progression",
    hover_data=['time'] # time value spot with the cursor
)
fig.update_layout(
    width=900,
    height=600,
    title=dict(x=0.5),
    coloraxis_colorbar=dict(title="Time (min)")
)
st.plotly_chart(fig, use_container_width=True)
st.markdown("Cardic drift refers to the gradual increase in heart rate during exercice. It is generarly observed a constant speed. Cardiac drift can be caused by dehydration, " \
"muscle fatigue or increased body temperature. In our case, we observe that at equivalent speeds, heart rate increases " \
"over time. This can be explained by muscle fatigue. Efficiency decreases and energy expenditure is slightly higher. " \
"This result is observed at both high and low speeds. The heart rate is higher at the end of the session than at the beginning. The " \
"heart increases more during speed interval and decreases less after speed intervals")

#----Cool down analysis
# Plot Graph : speed and heart rate
st.subheader("Cool-down analysis")
fig = make_subplots(specs=[[{"secondary_y": True}]])
# 1 - speed : scatter plot
fig.add_trace(go.Scatter(
    x=df_cooldown['time'],
    y=df_cooldown['enhanced_speed'],
    mode='lines',
    name='Speed (m/s)',
    line=dict(color='black', width=2)
), secondary_y=False)
# 2 - HR : scatter plot
fig.add_trace(go.Scatter(
    x=df_cooldown['time'],
    y=df_cooldown['heart_rate'],
    mode='lines',
    name='Heart Rate (bpm) cool_down',
    line=dict(color='blue', width=2)
), secondary_y=True)
# Add the average heart rate of the warm-up phase
fig.add_trace(go.Scatter(
    x=df_cooldown['time'],  
    y=[df_warmup['heart_rate'].mean()] * len(df_cooldown),  # all point of y with the same value
    mode='lines',
    name='Mean Heart Rate (warmup) bpm',
    line=dict(color='red', width=2, dash='dash')
), secondary_y=True)
fig.update_layout(
    title=dict(text="Speed (m/s) and heart rate over time", x=0.5, xanchor='center'),
    xaxis_title="Time",
    yaxis_title="Speed (m/s)",
    width=1200,
    height=600)
fig.update_yaxes(title_text="Heart Rate (bpm)", secondary_y=True)
st.plotly_chart(fig, use_container_width=True)
st.markdown("The cool-down phase is essential for recovery after intense exercise. It allows the heart rate to return to normal gradually and helps to eliminate metabolic waste products from the muscles. \n" \
            "In this cool-down phase, we can see that the speed has decreased, as has the heart rate. The heart rate gradually decreases. It may be important to gradually reduce the speed so that the heart "\
            "rate also decreases. \n" \
            "However, we note that, compared to the warm-up, the heart rate is higher. But it returns to the average " \
            "heart rate of the warm-up at the end of workout." )


st.subheader("Conclusion and overall analysis")
st.markdown("In conlusion, this is a high-intensity running session. Maintaining a workout like this with a return to normal heart rate, a fairly high cadence and a suitable length step indicates a good physical fitness and " \
"efficient running. A steady pace is another indicator of this fitness and running efficiency. \n" \
"You will feel tired at the end of the speed interval, but this is completely normal. \n" \
"To master short trails such as the Peak District, it may be beneficial to continue training like this while also increasing the distances, times and speed interval times. If you want to train on a track, it is important to increase and vary your interval sessions. In "\
"addition, low-intensity sessiosn should be added to accustom the boday to covering miles without exposing itself to injury. " \
"For example, no more thant two interval sessions should be done in a week. You need to add what are known as fundamental endurance sessions. " \
"In addition, it can be very beneficial to add muscle strengthening sessions to prevent injuries and strengthen the muscles needed for climbing and descending. " \
"Working out on the steps of the stadium stands can also be an alternative way to build strength. \n" \

"The ground and terrain can also be factors to consider when it comes to the difficulty of the race. Training on a track does " \
"not alllow you to develop your skills on uneven terrain. In other words, you will not be used to running on ground with holes, roots, stones or imperfections. " \
"This can be a problem. I recommend inclunding trainin in the forest, on trails or in the mountains il you can. \n"
"Track work will pose a problem on climbs and descents. This is because of the terrain is not flat. This can be problematic if the terrain is technical. " \
"In terms of muscles strength, following this advice may be a way to feel comfortable on short trails. ")

st.markdown("Finally, pay attention to the temperature. Your session took place in Nîmes at an average temprature of 26 degrees. This has an impact on performance and on the heart rate. In England, the temperature is likely to be lower," \
"which will affect how you feel while running.")
st.markdown("I wish you a great trail run and hope you perform as well as you hope to.")