
import streamlit as st
import pandas as pd
import numpy as np

# -----------------------------------------
# 1. Streamlit Page Configuration
# -----------------------------------------

st.set_page_config(
    page_title="Premier League Head-to-Head",
    page_icon="⚽",
    layout="wide"
)

# -----------------------------------------
# 2. Custom Background and Styling
# -----------------------------------------

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


# -----------------------------------------
# 3. Load Dataset
# -----------------------------------------

@st.cache_data
def load_data():

    url = "https://raw.githubusercontent.com/kkathait/D501_Final_Project/refs/heads/main/combined_data.csv"

    return pd.read_csv(url)


df = load_data()


# -----------------------------------------
# 4. Convert Date Column
# -----------------------------------------

df["Date"] = pd.to_datetime(
    df["Date"],
    dayfirst=True,
    errors="coerce"
)

# Remove rows with missing dates
df = df.dropna(subset=["Date"]).copy()


# -----------------------------------------
# 5. Identify Starting Year of Each Season
# -----------------------------------------

season_start = np.where(
    df["Date"].dt.month >= 8,
    df["Date"].dt.year,
    df["Date"].dt.year - 1
)

season_start = pd.Series(
    season_start,
    index=df.index
)


# -----------------------------------------
# 6. Create Season Labels
# -----------------------------------------

df["Season"] = (
    season_start.astype(str) + "/" +
    (season_start + 1).astype(str).str[-2:]
)


# -----------------------------------------
# 7. Check Season Counts and Date Ranges
# -----------------------------------------

season_counts = df.groupby("Season").size()

season_date_ranges = df.groupby("Season")["Date"].agg(
    ["min", "max"]
)

# Display in terminal / console
print("\nNumber of matches per season:")
print(season_counts)

print("\nDate ranges for each season:")
print(season_date_ranges)


# -----------------------------------------
# 8. Separate Dataset by Season
# -----------------------------------------

seasons = {
    season: data.copy()
    for season, data in df.groupby("Season")
}


# -----------------------------------------
# 9. Application Title
# -----------------------------------------

st.title("Premier League Head-to-Head Match History")


# -----------------------------------------
# 10. Season Overview
# -----------------------------------------

st.subheader("Premier League Season Overview")

season_overview = season_date_ranges.copy()

season_overview["Matches"] = season_counts

season_overview = season_overview.reset_index()

season_overview = season_overview.rename(
    columns={
        "min": "Start Date",
        "max": "End Date"
    }
)

season_overview = season_overview.sort_values(
    "Season",
    ascending=False
)

st.dataframe(
    season_overview,
    use_container_width=True,
    hide_index=True
)


# -----------------------------------------
# 11. Team Selection
# -----------------------------------------

teams = sorted(
    set(df["HomeTeam"]) | set(df["AwayTeam"])
)

col1, col2 = st.columns(2)

with col1:

    team1 = st.selectbox(
        "Select Team 1",
        teams
    )

with col2:

    team2_options = [
        team for team in teams
        if team != team1
    ]

    team2 = st.selectbox(
        "Select Team 2",
        team2_options
    )


# -----------------------------------------
# 12. Home Team Selection
# -----------------------------------------

home_team = st.radio(
    "Who is the Home Team?",
    [team1, team2]
)

away_team = (
    team2 if home_team == team1 else team1
)

st.write(f"**Home Team:** {home_team}")

st.write(f"**Away Team:** {away_team}")


# -----------------------------------------
# 13. Season Selection
# -----------------------------------------

st.subheader("Select Season")

available_seasons = sorted(
    df["Season"].dropna().unique(),
    reverse=True
)

selected_season = st.selectbox(
    "Choose a Season",
    ["All Seasons"] + available_seasons
)


# -----------------------------------------
# 14. Filter Matches
# -----------------------------------------

matches = df[
    (df["HomeTeam"] == home_team) &
    (df["AwayTeam"] == away_team)
].copy()


if selected_season != "All Seasons":

    matches = matches[
        matches["Season"] == selected_season
    ]


# -----------------------------------------
# 15. Match Summary
# -----------------------------------------

st.subheader("Match Summary")

st.write(
    f"These teams have played **{len(matches)}** times "
    f"with **{home_team} at home** and "
    f"**{away_team} away** "
    f"during **{selected_season}**."
)


if len(matches) == 0:

    st.warning(
        "No matches found for this selection."
    )

else:

    # -----------------------------------------
    # 16. Determine Match Winner
    # -----------------------------------------

    def winner(row):

        if row["FTR"] == "H":
            return row["HomeTeam"]

        elif row["FTR"] == "A":
            return row["AwayTeam"]

        else:
            return "Draw"


    matches["Winner"] = matches.apply(
        winner,
        axis=1
    )


    # -----------------------------------------
    # 17. Identify Red Card Columns
    # -----------------------------------------

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


    # -----------------------------------------
    # 18. Match History
    # -----------------------------------------

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
        "AR": "Away Red Cards",
        "HomeRedCards": "Home Red Cards",
        "AwayRedCards": "Away Red Cards"
    }


    st.dataframe(
        matches[display_cols]
        .sort_values(
            "Date",
            ascending=False
        )
        .rename(columns=rename_dict),
        use_container_width=True,
        hide_index=True
    )


    # -----------------------------------------
    # 19. Head-to-Head Statistics
    # -----------------------------------------

    st.subheader("Head-to-Head Statistics")

    home_team_goals = matches["FTHG"].sum()

    away_team_goals = matches["FTAG"].sum()

    home_wins = (
        matches["FTR"] == "H"
    ).sum()

    away_wins = (
        matches["FTR"] == "A"
    ).sum()

    draws = (
        matches["FTR"] == "D"
    ).sum()


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


    # -----------------------------------------
    # 20. Goal Totals
    # -----------------------------------------

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


    # -----------------------------------------
    # 21. Red Card Statistics
    # -----------------------------------------

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


    # -----------------------------------------
    # 22. Season-by-Season Statistics
    # -----------------------------------------

    st.subheader("Season-by-Season Comparison")

    season_stats = matches.groupby("Season").agg(

        Matches=("FTR", "count"),

        Home_Wins=(
            "FTR",
            lambda x: (x == "H").sum()
        ),

        Draws=(
            "FTR",
            lambda x: (x == "D").sum()
        ),

        Away_Wins=(
            "FTR",
            lambda x: (x == "A").sum()
        ),

        Home_Goals=("FTHG", "sum"),

        Away_Goals=("FTAG", "sum")

    ).reset_index()


    season_stats = season_stats.sort_values(
        "Season",
        ascending=False
    )


    st.dataframe(
        season_stats,
        use_container_width=True,
        hide_index=True
    )


    # -----------------------------------------
    # 23. End of Application
    # -----------------------------------------

    st.success(
        "Head-to-head analysis completed successfully!"
    )
