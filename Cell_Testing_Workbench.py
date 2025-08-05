# --------- Enhanced Battery Dashboard with CSV Export ---------
import streamlit as st
import random
import time
import pandas as pd
import matplotlib.pyplot as plt
import io

# --------- Utility Functions ---------
def get_cell_color(status):
    if status == 'charging':
        return 'background-color:#38ef7d'
    elif status == 'discharging':
        return 'background-color:#f7971e'
    else:
        return 'background-color:#5fa1f5'

def generate_random_temp():
    return round(random.uniform(25, 40), 1)

# --------- Initialize Session State ---------
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
    st.session_state.cells_data = {}
    st.session_state.cell_status = {}
    st.session_state.n_cells = 8
    st.session_state.cell_types = ['LFP'] * 8

# --------- Sidebar Navigation ---------
st.sidebar.markdown("## 🔋 **Cell Testing Workbench**")
pages = {
    'Dashboard': '📊 Dashboard',
    'Setup': '🛠️ Setup',
    'Control Panel': '🎛️ Control Panel',
    'Graph & Analysis': '📈 Graph & Analysis'
}
selected_label = st.sidebar.radio("Go to", list(pages.values()))
page = [k for k, v in pages.items() if v == selected_label][0]

# --------- Auto Refresh Setup (60 sec) ---------
import time
import streamlit as st

REFRESH_SEC = 60  # Refresh interval in seconds

# Manual refresh button
if st.button("🔄 Refresh Now"):
    st.rerun()

# Get last refresh time from query params
query_params = st.query_params
last_refresh_str = query_params.get('st_autorefresh', [None])[0]

try:
    last_refresh_time = float(last_refresh_str)
except (TypeError, ValueError):
    last_refresh_time = 0.0

# Auto-refresh if time exceeded
if time.time() - last_refresh_time > REFRESH_SEC:
    st.set_query_params(st_autorefresh=str(time.time()))
    st.rerun()

# --------- Setup Page ---------
if page == 'Setup':
    st.header("🛠️ Setup")

    name = st.text_input("Enter your bench name:", key='name')
    group = st.number_input("Enter your group number:", min_value=0, step=1, key='group')
    cell = st.selectbox("Select overall cell chemistry:", ['NMC', 'LFP'], key='cell_type')

    n_cells = st.slider("Number of cells:", 1, 8, st.session_state.n_cells, key='n_cells_slider')
    st.session_state.n_cells = n_cells

    if len(st.session_state.cell_types) != n_cells:
        st.session_state.cell_types = st.session_state.cell_types[:n_cells] + ['LFP'] * (n_cells - len(st.session_state.cell_types))

    for i in range(n_cells):
        st.session_state.cell_types[i] = st.selectbox(
            f"Type for Cell {i+1}:", ['LFP', 'NMC'],
            key=f'cell_{i+1}_type',
            index=['LFP', 'NMC'].index(st.session_state.cell_types[i])
        )

    if st.button('Initialize Cell Data'):
        st.session_state.cells_data = {}
        st.session_state.cell_status = {}
        for idx, cell_type in enumerate(st.session_state.cell_types, start=1):
            voltage = 3.2 if cell_type == "LFP" else 3.6
            min_voltage = 2.8 if cell_type == "LFP" else 3.2
            max_voltage = 3.6 if cell_type == "LFP" else 4.0
            current = 0.0
            temp = generate_random_temp()
            capacity = round(voltage * current, 2)
            keyname = f"cell_{idx}_{cell_type}"

            st.session_state.cells_data[keyname] = {
                "voltage": voltage,
                "current": current,
                "temp": temp,
                "capacity": capacity,
                "min_voltage": min_voltage,
                "max_voltage": max_voltage
            }
            st.session_state.cell_status[keyname] = "idle"
        st.session_state.initialized = True
        st.success("✅ Cells Initialized!")

# --------- Dashboard Page ---------
if page == 'Dashboard' and st.session_state.initialized:
    st.markdown("<h1 style='text-align: center;'>📊 Battery Dashboard Overview</h1>", unsafe_allow_html=True)

    total_charging = 0.0
    total_discharging = 0.0

    cell_keys = list(st.session_state.cells_data.keys())
    num_cells = len(cell_keys)
    cols_per_row = 4

    status_emojis = {
        'charging': '🔌',
        'discharging': '🔻',
        'idle': '🟦'
    }

    temp_emojis = lambda t: "🔥" if t > 37 else "🌡️" if t > 32 else "❄️"

    card_css = """
        <style>
            .battery-card {
                background: linear-gradient(135deg, #f8f9fa, #dee2e6);
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                margin-bottom: 20px;
                transition: all 0.3s ease-in-out;
                text-align: center;
            }
            .battery-card:hover {
                transform: scale(1.02);
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
            }
            .battery-card h5 {
                margin-bottom: 10px;
                font-size: 20px;
                color: #343a40;
            }
            .battery-card p {
                margin: 4px 0;
                font-size: 15px;
                color: #495057;
            }
        </style>
    """
    st.markdown(card_css, unsafe_allow_html=True)

    for row_start in range(0, num_cells, cols_per_row):
        cols = st.columns(cols_per_row)
        for i in range(cols_per_row):
            if row_start + i < num_cells:
                key = cell_keys[row_start + i]
                data = st.session_state.cells_data[key]
                status = st.session_state.cell_status[key]
                emoji = status_emojis.get(status, '⚙️')
                temp_icon = temp_emojis(data["temp"])

                if status == 'charging':
                    total_charging += data['capacity']
                elif status == 'discharging':
                    total_discharging += data['capacity']

                with cols[i]:
                    st.markdown(f"""
                        <div class="battery-card">
                            <h5>{emoji} {key.split('_')[0].capitalize()} {key.split('_')[1].upper()}</h5>
                            <p><b>Status:</b> {status.capitalize()} {emoji}</p>
                    """, unsafe_allow_html=True)

                    st.progress(min(data['capacity'] / 40, 1.0))

                    st.markdown(f"""
                            <p>🔋 <b>Voltage:</b> {data['voltage']} V</p>
                            <p>⚡ <b>Current:</b> {data['current']} A</p>
                            <p>{temp_icon} <b>Temp:</b> {data['temp']} °C</p>
                            <p>🔌 <b>Capacity:</b> {data['capacity']} Wh</p>
                        </div>
                    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    col1.success(f"🔋 **Total Charging Capacity**: {total_charging:.2f} Wh")
    col2.warning(f"🔻 **Total Discharging Capacity**: {total_discharging:.2f} Wh")

# --------- Control Panel Page ---------
if page == 'Control Panel' and st.session_state.initialized:
    st.header("🎛️ Control Panel")
    for key in st.session_state.cells_data:
        current = st.slider(f"Set current for {key}", -10.0, 10.0,
                            st.session_state.cells_data[key]["current"], 0.1, key=f'{key}_curr')
        if current > 0:
            st.session_state.cell_status[key] = 'charging'
        elif current < 0:
            st.session_state.cell_status[key] = 'discharging'
        else:
            st.session_state.cell_status[key] = 'idle'

        voltage = st.session_state.cells_data[key]['voltage']
        st.session_state.cells_data[key]['current'] = current
        st.session_state.cells_data[key]['capacity'] = round(voltage * abs(current), 2)
        st.session_state.cells_data[key]['temp'] = generate_random_temp()

# --------- Graph & Analysis Page ---------
if page == 'Graph & Analysis' and st.session_state.initialized:
    st.header("📈 Graph Representation & Analysis")
    df = pd.DataFrame(st.session_state.cells_data).T
    st.dataframe(df)

    st.subheader("📊 Cell Capacity Bar Chart")
    fig, ax = plt.subplots()
    status_colors = {'charging': '#38ef7d', 'discharging': '#f7971e', 'idle': '#5fa1f5'}
    bar_colors = [status_colors[st.session_state.cell_status[key]] for key in df.index]
    ax.bar(df.index, df['capacity'].values, color=bar_colors)
    plt.xticks(rotation=45)
    plt.ylabel('Capacity (Wh)')
    st.pyplot(fig)

    st.subheader("⚡ Voltage Profile")
    fig2, ax2 = plt.subplots()
    ax2.plot(df.index, df['voltage'].values, '-o')
    plt.xticks(rotation=45)
    plt.ylabel('Voltage (V)')
    st.pyplot(fig2)

    # --------- CSV Export ---------
    st.subheader("📤 Export Data")
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_buffer.getvalue(),
        file_name="battery_analysis.csv",
        mime="text/csv"
    )

# --------- Prompt Setup Warning ---------
if not st.session_state.initialized and page != 'Setup':
    st.info("🛠️ Please complete the Setup page to initialize cell data.")




