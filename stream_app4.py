
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Premier League Head-to-Head",
    page_icon="⚽",
    layout="wide"
)

# Custom Background and Styling
st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        135deg,
        #050B08 0%,
        #09291D 48%,
        #123D2A 100%
    );
    color: #FFFFFF;
}

h1 {
    color: #E8C76A !important;
    text-align: center;
    font-size: 38px !important;
    font-weight: 800 !important;
}

h2, h3 {
    color: #E8C76A !important;
    font-weight: 700 !important;
}

[data-testid="stMetric"] {
    background: rgba(20, 44, 32, 0.9);
    border: 1px solid #A8893C;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

[data-testid="stMetricValue"] {
    color: #E8C76A !important;
    font-weight: 800;
}

[data-testid="stMetricLabel"] {
    color: #FFFFFF !important;
}

.stSelectbox div[data-baseweb="select"] {
    background-color: #142C20;
    border-radius: 10px;
}

.stRadio {
    background: rgba(20, 44, 32, 0.8);
    padding: 12px;
    border-radius: 10px;
    border: 1px solid rgba(168, 137, 60, 0.5);
}

[data-testid="stDataFrame"] {
    border: 1px solid #A8893C;
    border-radius: 12px;
}

hr {
    border-color: #A8893C;

}
</style>
""", unsafe_allow_html=True)


# Load Data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/kkathait/D501_Final_Project/refs/heads/main/combined_data.csv"
    return pd.read_csv(url)

df = load_data()

# Convert Date column
df["Date"] = pd.to_datetime(df["Date"], dayfirst=True, errors="coerce")

# Create Season column
def get_season(date):
    if pd.isna(date):
        return None

    year = date.year

    if date.month >= 8:
        return f"{year}/{str(year + 1)[-2:]}"
    else:
        return f"{year - 1}/{str(year)[-2:]}"

df["Season"] = df["Date"].apply(get_season)

# Title
st.title("Premier League Head-to-Head Match History")

# Team Selection
teams = sorted(set(df["HomeTeam"]) | set(df["AwayTeam"]))

col1, col2 = st.columns(2)

with col1:
    team1 = st.selectbox("Select Team 1", teams)

with col2:
    team2 = st.selectbox(
        "Select Team 2",
        [team for team in teams if team != team1]
    )

# Home Team Selection
home_team = st.radio(
    "Who is the Home Team?",
    [team1, team2]
)

away_team = team2 if home_team == team1 else team1

st.write(f"**Home Team:** {home_team}")
st.write(f"**Away Team:** {away_team}")

# Season Selection
st.subheader("Select Season")

seasons = sorted(
    df["Season"].dropna().unique(),
    reverse=True
)

selected_season = st.selectbox(
    "Choose a Season",
    ["All Seasons"] + seasons
)

# Filter Matches
matches = df[
    (df["HomeTeam"] == home_team) &
    (df["AwayTeam"] == away_team)
].copy()

if selected_season != "All Seasons":
    matches = matches[
        matches["Season"] == selected_season
    ]

# Match Summary
st.subheader("Match Summary")

st.write(
    f"These teams have played **{len(matches)}** times "
    f"with **{home_team} at home** and "
    f"**{away_team} away** "
    f"during **{selected_season}**."
)

if len(matches) == 0:
    st.warning("No matches found for this selection.")

else:

    # Determine Winner
    def winner(row):
        if row["FTR"] == "H":
            return row["HomeTeam"]
        elif row["FTR"] == "A":
            return row["AwayTeam"]
        else:
            return "Draw"

    matches["Winner"] = matches.apply(winner, axis=1)

    # Red Card Columns
    home_red_col = None
    away_red_col = None

    for col in ["HR", "HomeRedCards"]:
        if col in matches.columns:
            home_red_col = col
            break

    for col in ["AR", "AwayRedCards"]:
        if col in matches.columns:
            away_red_col = col
            break

    # Match History
    st.subheader("Match History")

    display_cols = [
        "Season",
        "Date",
        "HomeTeam",
        "AwayTeam",
        "FTHG",
        "FTAG",
        "Winner"
    ]

    if home_red_col:
        display_cols.append(home_red_col)

    if away_red_col:
        display_cols.append(away_red_col)

    rename_dict = {
        "FTHG": "Home Goals",
        "FTAG": "Away Goals",
        "HR": "Home Red Cards",
        "AR": "Away Red Cards"
    }

    st.dataframe(
        matches[display_cols]
        .sort_values("Date", ascending=False)
        .rename(columns=rename_dict),
        use_container_width=True,
        hide_index=True
    )

    # Aggregate Statistics
    st.subheader("Head-to-Head Statistics")

    home_team_goals = matches["FTHG"].sum()
    away_team_goals = matches["FTAG"].sum()

    home_wins = (matches["FTR"] == "H").sum()
    away_wins = (matches["FTR"] == "A").sum()
    draws = (matches["FTR"] == "D").sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(f"{home_team} Wins", home_wins)
    col2.metric("Draws", draws)
    col3.metric(f"{away_team} Wins", away_wins)

    # Goal Totals
    st.subheader("Goal Totals")

    goal_col1, goal_col2 = st.columns(2)

    goal_col1.metric(
        f"{home_team} Goals",
        home_team_goals
    )

    goal_col2.metric(
        f"{away_team} Goals",
        away_team_goals
    )

    # Red Cards
    if home_red_col and away_red_col:

        st.subheader("Red Cards")

        red1, red2 = st.columns(2)

        red1.metric(
            f"{home_team} Red Cards",
            matches[home_red_col].sum()
        )

        red2.metric(
            f"{away_team} Red Cards",
            matches[away_red_col].sum()
        )

    # Season-by-Season Statistics
    st.subheader("Season-by-Season Comparison")

    season_stats = matches.groupby("Season").agg(
        Matches=("FTR", "count"),
        Home_Wins=("FTR", lambda x: (x == "H").sum()),
        Draws=("FTR", lambda x: (x == "D").sum()),
        Away_Wins=("FTR", lambda x: (x == "A").sum()),
        Home_Goals=("FTHG", "sum"),
        Away_Goals=("FTAG", "sum")
    ).reset_index()

    season_stats = season_stats.sort_values(
        "Season", ascending=False
    )

    st.dataframe(
        season_stats,
        use_container_width=True,
        hide_index=True
    )
