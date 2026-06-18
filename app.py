import streamlit as st
import snowflake.connector
import pandas as pd

# 1. PAGE SETUP: Must be the very first Streamlit command. Sets the browser tab title and expands the layout to use the full width of the screen.
st.set_page_config(page_title="IPL MDM Dashboard", layout="wide")

# 2. HEADER TEXT: Adds the titles and descriptive markdown to the top of your dashboard web page.
st.title("IPL Master Data Management Dashboard")
st.markdown("Built on Snowflake Medallion Architecture - Gold Layer Analytics")

# 3. DATABASE CONNECTION: 
# @st.cache_resource tells Streamlit to only establish this connection ONCE and share it globally.
# 'validate' automatically recreates the connection if Snowflake times out or disconnects behind the scenes.
@st.cache_resource(validate=lambda conn: conn.is_closed() == False)
def get_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],          # Pulls the secret username from your local secrets.toml or cloud settings
        password=st.secrets["snowflake"]["password"],  # Pulls the secret password securely without exposing it in the code
        account="cab40217.us-west-2",
        warehouse="COMPUTE_WH",
        database="IPL_MDM",
        schema="GOLD"
    )

# 4. DATA LOADING FUNCTIONS: 
# @st.cache_data remembers the tables pulled from SQL so the app doesn't keep spamming Snowflake with requests on every button click.
# NOTE: 'conn.close()' has been removed from these functions so the global cached connection stays open for all tabs.

@st.cache_data
def load_team_data():
    conn = get_connection() # Fetches our shared database connection
    # Executes the SQL query and automatically converts the tabular data into a Pandas DataFrame
    df = pd.read_sql("SELECT * FROM IPL_MDM.GOLD.TEAM_PERFORMANCE ORDER BY TOTAL_RUNS_SCORED DESC", conn)
    return df

@st.cache_data
def load_batter_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM IPL_MDM.GOLD.BATTER_PERFORMANCE ORDER BY TOTAL_RUNS DESC LIMIT 50", conn)
    return df

@st.cache_data
def load_bowler_data():
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM IPL_MDM.GOLD.BOWLER_PERFORMANCE ORDER BY WICKETS_TAKEN DESC LIMIT 50", conn)
    return df


# 5. USER INTERFACE NAVIGATION: Generates the clean horizontal navigation tabs across the dashboard.
tab1, tab2, tab3 = st.tabs(["Team Performance", "Batter Leaderboard", "Bowler Leaderboard"])


# ==========================================
# TAB 1: TEAM PERFORMANCE ANALSYSIS
# ==========================================
with tab1:
    st.subheader("IPL Team Performance Summary")
    team_df = load_team_data() # Loads the full dataframe containing all team metrics
    
    # SIDEBAR DESIGN: Puts a header inside the left sidebar panel
    st.sidebar.header("Dashboard Filters")
    all_teams = sorted(team_df["TEAM"].unique()) # Grabs an organized, alphabetical list of every team name
    
    # PRE-SELECTION LOGIC: Finds these 3 legendary teams in your data list to set them as defaults so your chart isn't empty on load
    default_teams = [team for team in ["Mumbai Indians", "Chennai Super Kings", "Royal Challengers Bangalore"] if team in all_teams]
    
    # MULTISELECT WIDGET: Renders a dropdown menu allowing users to add/remove multiple teams
    selected_teams = st.sidebar.multiselect(
        "Select Teams to Compare:",
        options=all_teams,
        default=default_teams if default_teams else all_teams[:3]
    )
    
    # PANDAS FILTERING: Keeps ONLY the rows belonging to the teams the user chose in the multiselect sidebar
    filtered_team_df = team_df[team_df["TEAM"].isin(selected_teams)]
    
    # CONDITIONAL UI: If the user selected at least one team, build the UI. If empty, show a warning.
    if not filtered_team_df.empty:
        # VISUAL LAYOUT: Cuts the page into 2 columns side-by-side to display KPI summary cards
        col1, col2 = st.columns(2)
        with col1:
            highest_runs = filtered_team_df["TOTAL_RUNS_SCORED"].max() # Finds highest run number in filtered data
            top_team = filtered_team_df.loc[filtered_team_df["TOTAL_RUNS_SCORED"].idxmax(), "TEAM"] # Finds the matching team name
            st.metric(label=f"Highest Runs Scored ({top_team})", value=f"{highest_runs:,}") # Formats number with commas
        with col2:
            total_teams = len(filtered_team_df) # Counts how many teams are currently checked
            st.metric(label="Teams Selected", value=total_teams)
            
        st.write("---") # Renders a clean horizontal line separator
        
        # BAR CHART VISUALIZATION: Dynamically updates to chart the selected teams along the X-axis against their runs scored on the Y-axis
        st.bar_chart(data=filtered_team_df, x="TEAM", y="TOTAL_RUNS_SCORED")
        
        st.write("---")
        
        # DATA TABLE VIEW: Renders the structured data rows below the visual chart
        st.dataframe(filtered_team_df, use_container_width=True)
    else:
        # Handles the empty state if a user clears all choices from the sidebar selection
        st.warning("Please select at least one team from the sidebar to view analytics.")


# ==========================================
# TAB 2: BATTER LEADERBOARD
# ==========================================
with tab2:
    st.subheader("Top 50 Batters by Total Runs")
    batter_df = load_batter_data() # Pulls top 50 batters
    
    # SEARCH FILTER: Text input box where users type a player's name
    search = st.text_input("Search by batter name")
    if search:
        # If the user typed something, filter the 'BATTER' column. 'case=False' means 'kohli' matches 'Kohli'.
        batter_df = batter_df[batter_df["BATTER"].str.contains(search, case=False)]
        
    st.dataframe(batter_df, use_container_width=True)


# ==========================================
# TAB 3: BOWLER LEADERBOARD
# ==========================================
with tab3:
    st.subheader("Top 50 Bowlers by Wickets Taken")
    bowler_df = load_bowler_data() # Pulls top 50 bowlers
    
    # SEARCH FILTER: Text input box for looking up bowlers
    search2 = st.text_input("Search by bowler name")
    if search2:
        # Dynamically scales down the dataset rows based on string character matching
        bowler_df = bowler_df[bowler_df["BOWLER"].str.contains(search2, case=False)]
        
    st.dataframe(bowler_df, use_container_width=True)