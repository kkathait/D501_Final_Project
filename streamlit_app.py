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