import pandas as pd

# First we create a records table


def create_results_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_wins = (home_games["FTR"] == "H").sum()
        home_losses = (home_games["FTR"] == "A").sum()
        home_draws = (home_games["FTR"] == "D").sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_wins = (away_games["FTR"] == "A").sum()
        away_losses = (away_games["FTR"] == "H").sum()
        away_draws = (away_games["FTR"] == "D").sum()

        records.append({
            "Team": team,
            "Wins": home_wins + away_wins,
            "Losses": home_losses + away_losses,
            "Draws": home_draws + away_draws,
            "Games": (
                home_wins + away_wins
                + home_losses + away_losses
                + home_draws + away_draws
            )
        })

    results = pd.DataFrame(records)

    return results


# Next we create a win percentage table
def create_standings_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_wins = (home_games["FTR"] == "H").sum()
        home_losses = (home_games["FTR"] == "A").sum()
        home_draws = (home_games["FTR"] == "D").sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_wins = (away_games["FTR"] == "A").sum()
        away_losses = (away_games["FTR"] == "H").sum()
        away_draws = (away_games["FTR"] == "D").sum()

        records.append({
            "Team": team,
            "Home Games": home_wins + home_losses + home_draws,
            "Home Win Percentage": (home_wins / (home_wins + home_draws + home_losses)).round(3),
            "Home Point Percentage": ((home_wins + home_draws) / (home_wins + home_draws + home_losses)).round(3),
            "Road Games": away_wins + away_losses + away_draws,
            "Road Win Percentage": (away_wins / (away_wins + away_draws + away_losses)).round(3),
            "Road Point Percentage": ((away_wins + away_draws) / (away_wins + away_draws + away_losses)).round(3)
        })

    standings = pd.DataFrame(records)

    return standings


# Create a shots table
def create_shots_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_goals_for = home_games["FTHG"].sum()
        home_shots_for = home_games["HS"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_goals_for = away_games["FTAG"].sum()
        away_shots_for = away_games["AS"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "Shots Home": home_shots_for,
            "Goals Home": home_goals_for,
            "Home Shots per Goal": home_shots_for / home_goals_for if home_goals_for > 0 else 0,
            "Home Shots per Game": home_shots_for / (len(home_games) if len(home_games) > 0 else 1),
            "Shots Away": away_shots_for,
            "Goals Away": away_goals_for,
            "Away Shots per Goal": away_shots_for / away_goals_for if away_goals_for > 0 else 0,
            "Away Shots per Game": away_shots_for / (len(away_games) if len(away_games) > 0 else 1)
        })

    shots = pd.DataFrame(records)

    shots["Home Shots per Goal"] = shots["Home Shots per Goal"].round(2)
    shots["Home Shots per Game"] = shots["Home Shots per Game"].round(2)
    shots["Away Shots per Goal"] = shots["Away Shots per Goal"].round(2)
    shots["Away Shots per Game"] = shots["Away Shots per Game"].round(2)

    return shots


# Create shots against table
def create_shots_against_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_goals_against = home_games["FTAG"].sum()
        home_shots_against = home_games["AS"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_goals_against = away_games["FTHG"].sum()
        away_shots_against = away_games["HS"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "Shots Allowed Home": home_shots_against,
            "Goals Allowed Home": home_goals_against,
            "Home Opp Shots per Goal": home_shots_against / home_goals_against if home_goals_against > 0 else 0,
            "Home Opp Shots per Game": home_shots_against / (len(home_games) if len(home_games) > 0 else 1),
            "Shots Allowed Away": away_shots_against,
            "Goals Allowed Away": away_goals_against,
            "Away Opp Shots per Goal": away_shots_against / away_goals_against if away_goals_against > 0 else 0,
            "Away Opp Shots per Game": away_shots_against / (len(away_games) if len(away_games) > 0 else 1)
        })

    shots_against = pd.DataFrame(records)

    shots_against["Home Opp Shots per Goal"] = shots_against["Home Opp Shots per Goal"].round(
        2)
    shots_against["Home Opp Shots per Game"] = shots_against["Home Opp Shots per Game"].round(
        2)
    shots_against["Away Opp Shots per Goal"] = shots_against["Away Opp Shots per Goal"].round(
        2)
    shots_against["Away Opp Shots per Game"] = shots_against["Away Opp Shots per Game"].round(
        2)

    return shots_against


# Create a shots on target table
def create_shots_target_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_sot = home_games["HST"].sum()
        home_shots_for = home_games["HS"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_sot = away_games["AST"].sum()
        away_shots_for = away_games["AS"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "Shots on Target Home": home_sot,
            "Percent SOT Home": home_sot / home_shots_for if home_shots_for > 0 else 0,
            "Shots on Target Away": away_sot,
            "Percent SOT Away": away_sot / away_shots_for if away_shots_for > 0 else 0,
        })

    sot = pd.DataFrame(records)

    sot["Percent SOT Home"] = sot["Percent SOT Home"].round(2)
    sot["Percent SOT Away"] = sot["Percent SOT Away"].round(2)

    return sot


# Create a shots on target against table
def create_shots_target_against_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_sot_against = home_games["AST"].sum()
        home_shots_against = home_games["AS"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_sot_against = away_games["HST"].sum()
        away_shots_against = away_games["HS"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "SOT Allowed Home": home_sot_against,
            "Percent SOT Allowed Home": home_sot_against / home_shots_against if home_shots_against > 0 else 0,
            "SOT Allowed Away": away_sot_against,
            "Percent SOT Allowed Away": away_sot_against / away_shots_against if away_shots_against > 0 else 0,
        })

    sot_against = pd.DataFrame(records)

    sot_against["Percent SOT Allowed Home"] = sot_against["Percent SOT Allowed Home"].round(
        2)
    sot_against["Percent SOT Allowed Away"] = sot_against["Percent SOT Allowed Away"].round(
        2)

    return sot_against


# Create corners table
def create_corners_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_corn = home_games["HC"].sum()
        home_corn_allowed = home_games["AC"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_corn = away_games["AC"].sum()
        away_corn_allowed = away_games["HC"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "Corners Home": home_corn,
            "Corners Home per Game": home_corn / len(home_games) if len(home_games) > 0 else np.nan,
            "Corners Away": away_corn,
            "Corners Away per Game": away_corn / len(away_games) if len(away_games) > 0 else np.nan,
            "Corners Allowed Home": home_corn_allowed,
            "Corners Allowed Home per Game": home_corn_allowed / len(home_games) if len(home_games) > 0 else np.nan,
            "Corners Allowed Away": away_corn_allowed,
            "Corners Allowed Away per Game": away_corn_allowed / len(away_games) if len(away_games) > 0 else np.nan
        })

    corners = pd.DataFrame(records)

    corners["Corners Home per Game"] = corners["Corners Home per Game"].round(
        1)
    corners["Corners Away per Game"] = corners["Corners Away per Game"].round(
        1)
    corners["Corners Allowed Home per Game"] = corners["Corners Allowed Home per Game"].round(
        1)
    corners["Corners Allowed Away per Game"] = corners["Corners Allowed Away per Game"].round(
        1)

    return corners


# Create fouls table
def create_fouls_table(url):
    df_premier = pd.read_csv(url)

    teams = sorted(
        set(df_premier["HomeTeam"]) |
        set(df_premier["AwayTeam"])
    )

    records = []

    for team in teams:
        home_games = df_premier[df_premier["HomeTeam"] == team]

        home_fouls = home_games["HF"].sum()
        home_yellows = home_games["HY"].sum()
        home_reds = home_games["HR"].sum()

        away_games = df_premier[df_premier["AwayTeam"] == team]

        away_fouls = away_games["AF"].sum()
        away_yellows = away_games["AY"].sum()
        away_reds = away_games["AR"].sum()

        records.append({
            "Team": team,
            "Games": len(home_games) + len(away_games),
            "Fouls": home_fouls + away_fouls,
            "Yellows": home_yellows + away_yellows,
            "Yellows per Game": (home_yellows + away_yellows) / (len(home_games) + len(away_games)) if (len(home_games) + len(away_games)) > 0 else np.nan,
            "Reds": home_reds + away_reds,
            "Reds per Game": (home_reds + away_reds) / (len(home_games) + len(away_games)) if (len(home_games) + len(away_games)) > 0 else np.nan,
            "Booking Points": (home_yellows + away_yellows) * 10 + (home_reds + away_reds) * 25,
            "Booking Points per Game": ((home_yellows + away_yellows) * 10 + (home_reds + away_reds) * 25) / (len(home_games) + len(away_games)) if (len(home_games) + len(away_games)) > 0 else np.nan
        })

    fouls = pd.DataFrame(records)

    fouls["Yellows per Game"] = fouls["Yellows per Game"].round(2)
    fouls["Reds per Game"] = fouls["Reds per Game"].round(2)
    fouls["Booking Points per Game"] = fouls["Booking Points per Game"].round(
        2)

    return fouls
