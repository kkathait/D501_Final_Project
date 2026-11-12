"""Train and use a leakage-safe LightGBM model for Premier League match results."""

from __future__ import annotations

import argparse
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import lightgbm as lgb
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, log_loss


DATA_PATH = Path(__file__).with_name("combined_data.csv")
MODEL_PATH = Path(__file__).with_name("lightgbm_match_result.txt")
OUTCOMES = ("H", "D", "A")
TEAM_COLUMNS = ("home_team", "away_team")

MATCH_STATS = {
    "goals_for": ("FTHG", "FTAG"),
    "goals_against": ("FTAG", "FTHG"),
    "shots_for": ("HS", "AS"),
    "shots_against": ("AS", "HS"),
    "shots_on_target_for": ("HST", "AST"),
    "shots_on_target_against": ("AST", "HST"),
    "fouls": ("HF", "AF"),
    "corners_for": ("HC", "AC"),
    "corners_against": ("AC", "HC"),
    "yellow_cards": ("HY", "AY"),
    "red_cards": ("HR", "AR"),
}
REQUIRED_COLUMNS = {
    "Date", "Time", "HomeTeam", "AwayTeam", "FTR",
    *(column for columns in MATCH_STATS.values() for column in columns),
}


def _new_team_state() -> dict[str, Any]:
    state: dict[str, Any] = {
        "games": 0,
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "points": 0,
        "recent_points": deque(maxlen=5),
        "recent_goals_for": deque(maxlen=5),
        "recent_goals_against": deque(maxlen=5),
    }
    for venue in ("home", "away"):
        state[venue] = {
            "games": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "points": 0,
        }
        for stat in MATCH_STATS:
            state[venue][stat] = 0.0
    for stat in MATCH_STATS:
        state[stat] = 0.0
    return state


def _rate(total: float, count: int) -> float:
    return total / count if count else float("nan")


def _side_features(state: dict[str, Any], venue: str) -> dict[str, float]:
    games = state["games"]
    venue_state = state[venue]
    venue_games = venue_state["games"]
    result: dict[str, float] = {
        "games": float(games),
        "wins": float(state["wins"]),
        "draws": float(state["draws"]),
        "losses": float(state["losses"]),
        "win_pct": _rate(state["wins"], games),
        "point_pct": _rate(state["points"], 3 * games),
        "venue_games": float(venue_games),
        "venue_wins": float(venue_state["wins"]),
        "venue_draws": float(venue_state["draws"]),
        "venue_losses": float(venue_state["losses"]),
        "venue_win_pct": _rate(venue_state["wins"], venue_games),
        "venue_point_pct": _rate(venue_state["points"], 3 * venue_games),
        "form_points_last5": _rate(sum(state["recent_points"]), len(state["recent_points"])),
        "form_goals_for_last5": _rate(
            sum(state["recent_goals_for"]), len(state["recent_goals_for"])
        ),
        "form_goals_against_last5": _rate(
            sum(state["recent_goals_against"]), len(state["recent_goals_against"])
        ),
    }
    for stat in MATCH_STATS:
        overall_rate = _rate(state[stat], games)
        venue_rate = _rate(venue_state[stat], venue_games)
        result[f"{stat}_per_game"] = overall_rate
        result[f"{stat}_per_game_venue"] = venue_rate

    result["shots_per_goal"] = _rate(state["shots_for"], state["goals_for"])
    result["opponent_shots_per_goal"] = _rate(
        state["shots_against"], state["goals_against"]
    )
    result["shots_per_goal_venue"] = _rate(
        venue_state["shots_for"], venue_state["goals_for"]
    )
    result["opponent_shots_per_goal_venue"] = _rate(
        venue_state["shots_against"], venue_state["goals_against"]
    )
    result["booking_points_per_game"] = _rate(
        state["yellow_cards"] * 10 + state["red_cards"] * 25, games
    )
    result["booking_points_per_game_venue"] = _rate(
        venue_state["yellow_cards"] * 10 + venue_state["red_cards"] * 25,
        venue_games,
    )
    result["shots_on_target_pct"] = _rate(
        state["shots_on_target_for"], state["shots_for"]
    )
    result["shots_on_target_allowed_pct"] = _rate(
        state["shots_on_target_against"], state["shots_against"]
    )
    result["shots_on_target_pct_venue"] = _rate(
        venue_state["shots_on_target_for"], venue_state["shots_for"]
    )
    result["shots_on_target_allowed_pct_venue"] = _rate(
        venue_state["shots_on_target_against"], venue_state["shots_against"]
    )
    return result


def _update_team_state(
    state: dict[str, Any],
    venue: str,
    outcome: str,
    row: pd.Series,
    side: str,
) -> None:
    venue_state = state[venue]
    venue_state["games"] += 1
    state["games"] += 1

    if outcome == "D":
        venue_state["draws"] += 1
        state["draws"] += 1
        venue_state["points"] += 1
        state["points"] += 1
        points = 1
    else:
        won = (venue == "home" and outcome == "H") or (
            venue == "away" and outcome == "A"
        )
        result_key = "wins" if won else "losses"
        venue_state[result_key] += 1
        state[result_key] += 1
        if won:
            venue_state["points"] += 3
            state["points"] += 3
        points = 3 if won else 0

    goals_for = float(row["FTHG"] if side == "home" else row["FTAG"])
    goals_against = float(row["FTAG"] if side == "home" else row["FTHG"])
    state["recent_points"].append(points)
    state["recent_goals_for"].append(goals_for)
    state["recent_goals_against"].append(goals_against)

    for stat, columns in MATCH_STATS.items():
        value = row[columns[0] if side == "home" else columns[1]]
        if pd.notna(value):
            state[stat] += float(value)
            venue_state[stat] += float(value)


def _prepare_matches(matches: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(matches.columns)
    if missing:
        raise ValueError(f"Match data is missing required columns: {sorted(missing)}")

    matches = matches.copy()
    matches = matches[matches["FTR"].isin(OUTCOMES)].copy()
    if matches.empty:
        raise ValueError("No completed matches with FTR values H, D, or A were found.")

    matches["_kickoff"] = pd.to_datetime(
        matches["Date"].astype(str) + " " + matches["Time"].fillna("00:00").astype(str),
        dayfirst=True,
        errors="coerce",
    )
    if matches["_kickoff"].isna().any():
        raise ValueError("Some completed matches have an invalid Date or Time.")

    numeric_columns = {
        column for columns in MATCH_STATS.values() for column in columns
    }
    for column in numeric_columns:
        matches[column] = pd.to_numeric(matches[column], errors="coerce")

    return matches.sort_values("_kickoff", kind="stable").reset_index(drop=True)


def build_match_features(
    matches: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, dict[str, dict[str, Any]], list[str]]:
    """Build pre-match features, labels, and final team histories from match rows."""
    data = _prepare_matches(matches)
    states: defaultdict[str, dict[str, Any]] = defaultdict(_new_team_state)
    feature_rows: list[dict[str, Any]] = []

    for _, kickoff_group in data.groupby("_kickoff", sort=False):
        group_features: list[dict[str, Any]] = []
        for _, row in kickoff_group.iterrows():
            home_state = states[row["HomeTeam"]]
            away_state = states[row["AwayTeam"]]
            features: dict[str, Any] = {
                "home_team": row["HomeTeam"],
                "away_team": row["AwayTeam"],
            }
            features.update({
                f"home_{name}": value
                for name, value in _side_features(home_state, "home").items()
            })
            features.update({
                f"away_{name}": value
                for name, value in _side_features(away_state, "away").items()
            })
            group_features.append(features)
        feature_rows.extend(group_features)

        for (_, row), features in zip(kickoff_group.iterrows(), group_features):
            _update_team_state(
                states[row["HomeTeam"]], "home", row["FTR"], row, "home"
            )
            _update_team_state(
                states[row["AwayTeam"]], "away", row["FTR"], row, "away"
            )

    features_frame = pd.DataFrame(feature_rows)
    teams = sorted(set(data["HomeTeam"]) | set(data["AwayTeam"]))
    for column in TEAM_COLUMNS:
        features_frame[column] = pd.Categorical(
            features_frame[column], categories=teams
        )
    labels = data["FTR"].reset_index(drop=True)
    return features_frame, labels, dict(states), teams


def train_model(
    matches: pd.DataFrame,
) -> tuple[lgb.LGBMClassifier, dict[str, float], dict[str, dict[str, Any]], list[str]]:
    """Evaluate chronologically, then fit the final classifier on all completed matches."""
    features, labels, team_states, teams = build_match_features(matches)
    if len(features) < 30:
        raise ValueError("At least 30 completed matches are required to train and evaluate.")

    split_at = int(len(features) * 0.8)
    train_features, test_features = features.iloc[:split_at], features.iloc[split_at:]
    train_labels, test_labels = labels.iloc[:split_at], labels.iloc[split_at:]
    if len(set(train_labels)) < 2 or len(set(test_labels)) < 2:
        raise ValueError(
            "The chronological train/test split needs at least two result classes "
            "in both partitions."
        )

    model_options = {
        "objective": "multiclass",
        "num_class": len(OUTCOMES),
        "n_estimators": 300,
        "learning_rate": 0.03,
        "num_leaves": 15,
        "min_child_samples": 15,
        "subsample": 0.9,
        "subsample_freq": 1,
        "colsample_bytree": 0.9,
        "random_state": 42,
        "verbosity": -1,
    }
    evaluation_model = lgb.LGBMClassifier(**model_options)
    evaluation_model.fit(train_features, train_labels)
    test_probabilities = evaluation_model.predict_proba(test_features)
    predictions = evaluation_model.classes_[test_probabilities.argmax(axis=1)]
    metrics = {
        "accuracy": float(accuracy_score(test_labels, predictions)),
        "macro_f1": float(f1_score(
            test_labels,
            predictions,
            labels=list(OUTCOMES),
            average="macro",
            zero_division=0,
        )),
        "log_loss": float(log_loss(
            test_labels, test_probabilities, labels=evaluation_model.classes_
        )),
        "test_matches": float(len(test_labels)),
    }

    final_model = lgb.LGBMClassifier(**model_options)
    final_model.fit(features, labels)
    return final_model, metrics, team_states, teams


def predict_match(
    model: lgb.LGBMClassifier,
    home_team: str,
    away_team: str,
    team_states: dict[str, dict[str, Any]],
    teams: list[str],
) -> dict[str, Any]:
    """Return all three outcome probabilities for a future fixture."""
    if home_team not in teams or away_team not in teams:
        unknown = [team for team in (home_team, away_team) if team not in teams]
        raise ValueError(f"Unknown team name(s): {', '.join(unknown)}")
    if home_team == away_team:
        raise ValueError("Home and away teams must be different.")

    home_state = team_states.get(home_team, _new_team_state())
    away_state = team_states.get(away_team, _new_team_state())
    features: dict[str, Any] = {
        "home_team": home_team,
        "away_team": away_team,
    }
    features.update({
        f"home_{name}": value
        for name, value in _side_features(home_state, "home").items()
    })
    features.update({
        f"away_{name}": value
        for name, value in _side_features(away_state, "away").items()
    })
    input_frame = pd.DataFrame([features])
    for column in TEAM_COLUMNS:
        input_frame[column] = pd.Categorical(input_frame[column], categories=teams)

    probabilities = model.predict_proba(input_frame)[0]
    outcome_probabilities = {
        str(outcome): float(probability)
        for outcome, probability in zip(model.classes_, probabilities)
    }
    predicted_outcome = max(outcome_probabilities, key=outcome_probabilities.get)
    return {
        "outcome": predicted_outcome,
        "home_team": home_team,
        "away_team": away_team,
        "home_win_probability": outcome_probabilities.get("H", 0.0),
        "draw_probability": outcome_probabilities.get("D", 0.0),
        "away_win_probability": outcome_probabilities.get("A", 0.0),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train a LightGBM model and optionally predict a fixture."
    )
    parser.add_argument("--home-team", help="Home team name for a fixture prediction.")
    parser.add_argument("--away-team", help="Away team name for a fixture prediction.")
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_PATH,
        help=f"CSV match data (default: {DATA_PATH.name}).",
    )
    args = parser.parse_args()
    if bool(args.home_team) != bool(args.away_team):
        parser.error("--home-team and --away-team must be provided together.")

    matches = pd.read_csv(args.data)
    model, metrics, team_states, teams = train_model(matches)
    model.booster_.save_model(str(MODEL_PATH))

    print(f"Chronological holdout ({int(metrics['test_matches'])} matches):")
    print(f"  Accuracy: {metrics['accuracy']:.3f}")
    print(f"  Macro F1:  {metrics['macro_f1']:.3f}")
    print(f"  Log loss:  {metrics['log_loss']:.3f}")
    print(f"Final model saved to {MODEL_PATH}")

    if args.home_team and args.away_team:
        result = predict_match(
            model, args.home_team, args.away_team, team_states, teams
        )
        print(
            f"\n{result['home_team']} vs {result['away_team']}: "
            f"most likely result = {result['outcome']}"
        )
        print(f"  Home win: {result['home_win_probability']:.1%}")
        print(f"  Draw:     {result['draw_probability']:.1%}")
        print(f"  Away win: {result['away_win_probability']:.1%}")


if __name__ == "__main__":
    main()