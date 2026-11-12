import streamlit as st
import pandas as pd

# Load data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/kkathait/D501_Final_Project/refs/heads/main/combined_data.csv"
    return pd.read_csv(url)

df = load_data()

st.title("Premier League Head-to-Head Match History")

# Team list
teams = sorted(set(df["HomeTeam"]) | set(df["AwayTeam"]))

team1 = st.selectbox("Select Team 1", teams)
team2 = st.selectbox(
    "Select Team 2",
    [team for team in teams if team != team1]
)

home_team = st.radio(
    "Who is the Home Team?",
    [team1, team2]
)

if home_team == team1:
    away_team = team2
else:
    away_team = team1

st.write(f"**Home Team:** {home_team}")
st.write(f"**Away Team:** {away_team}")

# Filter matches
matches = df[
    (df["HomeTeam"] == home_team) &
    (df["AwayTeam"] == away_team)
].copy()

st.subheader("Match Summary")

st.write(
    f"These teams have played **{len(matches)}** times with "
    f"**{home_team} at home** and **{away_team} away**."
)

if len(matches) == 0:
    st.warning("No matches found.")
else:

    # Determine winner
    def winner(row):
        if row["FTR"] == "H":
            return row["HomeTeam"]
        elif row["FTR"] == "A":
            return row["AwayTeam"]
        else:
            return "Draw"

    matches["Winner"] = matches.apply(winner, axis=1)

    # Red card columns check
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

    display_cols = [
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

    st.dataframe(
        matches[display_cols]
        .rename(columns={
            "FTHG": "Home Goals",
            "FTAG": "Away Goals",
            "HR": "Home Red Cards",
            "AR": "Away Red Cards"
        })
    )

    # Aggregate Statistics
    st.subheader("Head-to-Head Statistics")

    home_team_goals = matches["FTHG"].sum()
    away_team_goals = matches["FTAG"].sum()

    home_wins = (matches["FTR"] == "H").sum()
    away_wins = (matches["FTR"] == "A").sum()
    draws = (matches["FTR"] == "D").sum()

    col1, col2, col3 = st.columns(3)

    col1.metric(
        f"{home_team} Wins",
        home_wins
    )

    col2.metric(
        "Draws",
        draws
    )

    col3.metric(
        f"{away_team} Wins",
        away_wins
    )

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

        
# ==========================================
# PREMIER LEAGUE VISUALIZATION DASHBOARD
# ==========================================

st.title("Premier League Performance Dashboard")

# Create standings
teams = sorted(set(df["HomeTeam"]) | set(df["AwayTeam"]))

records = []

for team in teams:

    home = df[df["HomeTeam"] == team]
    away = df[df["AwayTeam"] == team]

    wins = (
        (home["FTR"] == "H").sum() +
        (away["FTR"] == "A").sum()
    )

    draws = (
        (home["FTR"] == "D").sum() +
        (away["FTR"] == "D").sum()
    )

    losses = (
        (home["FTR"] == "A").sum() +
        (away["FTR"] == "H").sum()
    )

    goals_for = home["FTHG"].sum() + away["FTAG"].sum()

    goals_against = home["FTAG"].sum() + away["FTHG"].sum()

    records.append({
        "Team": team,
        "Played": wins + draws + losses,
        "Wins": wins,
        "Draws": draws,
        "Losses": losses,
        "Goals For": goals_for,
        "Goals Against": goals_against,
        "Goal Difference": goals_for - goals_against,
        "Points": wins * 3 + draws
    })

standings = pd.DataFrame(records)

standings = standings.sort_values(
    ["Points", "Goal Difference", "Goals For"],
    ascending=False
).reset_index(drop=True)

standings.insert(0, "Position", range(1, len(standings) + 1))

# LEAGUE TABLE
st.subheader("Premier League Standings")

st.dataframe(
    standings,
    use_container_width=True,
    hide_index=True
)

# POINTS CHART
st.subheader("Points by Team")

st.bar_chart(
    standings.set_index("Team")[["Points"]],
    color="#3498db"
)

# MATCH RESULTS CHART
st.subheader("Wins, Draws and Losses")

st.bar_chart(
    standings.set_index("Team")[["Wins", "Draws", "Losses"]],
    color=["#2ecc71", "#f1c40f", "#e74c3c"]
)

# GOALS CHART
st.subheader("Goals Scored vs Goals Conceded")

st.bar_chart(
    standings.set_index("Team")[["Goals For", "Goals Against"]],
    color=["#3498db", "#e74c3c"]
)

# TEAM SELECTION
st.subheader("Individual Team Analysis")

selected_team = st.selectbox(
    "Select a team",
    standings["Team"].tolist(),
    key="individual_team"
)

team_data = standings[
    standings["Team"] == selected_team
].iloc[0]

# TEAM METRICS
col1, col2, col3, col4 = st.columns(4)

col1.metric("Position", int(team_data["Position"]))
col2.metric("Points", int(team_data["Points"]))
col3.metric("Wins", int(team_data["Wins"]))
col4.metric("Goal Difference", int(team_data["Goal Difference"]))

# TEAM RESULTS VISUALIZATION
st.subheader(f"{selected_team} Match Results")

team_results = pd.DataFrame({
    "Result": ["Wins", "Draws", "Losses"],
    "Matches": [
        team_data["Wins"],
        team_data["Draws"],
        team_data["Losses"]
    ]
})

st.bar_chart(
    team_results.set_index("Result"),
    color="#3498db"
)


