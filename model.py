"""Train and use an XGBoost model for Premier League match results."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer, make_column_selector
from sklearn.metrics import accuracy_score, f1_score, log_loss
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from modelpredictive import (
    OUTCOMES,
    TEAM_COLUMNS,
    _new_team_state,
    _prepare_matches,
    _side_features,
    build_match_features,
)


DATA_PATH = Path(__file__).with_name("combined_data.csv")
MODEL_PATH = Path(__file__).with_name("xgboost_match_result.joblib")
LABEL_TO_INDEX = {outcome: index for index, outcome in enumerate(OUTCOMES)}
INITIAL_ELO = 1500.0
ELO_K_FACTOR = 32.0
HOME_ADVANTAGE_ELO = 60.0


def _build_elo_features(
    matches: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Build Elo ratings using only results from earlier kickoff times."""
    data = _prepare_matches(matches)
    ratings: defaultdict[str, float] = defaultdict(lambda: INITIAL_ELO)
    feature_rows: list[dict[str, float]] = []

    for _, kickoff_group in data.groupby("_kickoff", sort=False):
        group_features: list[dict[str, float]] = []
        for _, row in kickoff_group.iterrows():
            home_rating = ratings[row["HomeTeam"]]
            away_rating = ratings[row["AwayTeam"]]
            group_features.append({
                "home_elo": home_rating,
                "away_elo": away_rating,
                "elo_difference": home_rating + HOME_ADVANTAGE_ELO - away_rating,
            })
        feature_rows.extend(group_features)

        for (_, row), features in zip(kickoff_group.iterrows(), group_features):
            expected_home_score = 1.0 / (
                1.0 + 10.0 ** (-features["elo_difference"] / 400.0)
            )
            actual_home_score = {"H": 1.0, "D": 0.5, "A": 0.0}[row["FTR"]]
            rating_change = ELO_K_FACTOR * (
                actual_home_score - expected_home_score
            )
            ratings[row["HomeTeam"]] += rating_change
            ratings[row["AwayTeam"]] -= rating_change

    return pd.DataFrame(feature_rows), dict(ratings)


def _new_model() -> Pipeline:
    preprocessing = ColumnTransformer(
        transformers=[
            ("teams", OneHotEncoder(handle_unknown="ignore"), list(TEAM_COLUMNS)),
            (
                "numeric",
                SimpleImputer(strategy="median", keep_empty_features=True),
                make_column_selector(dtype_include="number"),
            ),
        ],
    )
    classifier = XGBClassifier(
        objective="multi:softprob",
        num_class=len(OUTCOMES),
        eval_metric="mlogloss",
        n_estimators=300,
        max_depth=1,
        learning_rate=0.03,
        min_child_weight=10,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        tree_method="hist",
    )
    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("classifier", classifier),
        ]
    )


def train_model(
    matches: pd.DataFrame,
) -> tuple[Pipeline, dict[str, float], dict[str, dict[str, Any]], list[str]]:
    """Evaluate on the latest 20% of matches, then fit on all completed matches."""
    features, labels, team_states, teams = build_match_features(matches)
    elo_features, final_ratings = _build_elo_features(matches)
    features = pd.concat([features, elo_features], axis=1)
    for team, rating in final_ratings.items():
        team_states[team]["elo_rating"] = rating
    if len(features) < 30:
        raise ValueError("At least 30 completed matches are required to train and evaluate.")

    encoded_labels = labels.map(LABEL_TO_INDEX)
    split_at = int(len(features) * 0.8)
    train_features, test_features = features.iloc[:split_at], features.iloc[split_at:]
    train_labels, test_labels = encoded_labels.iloc[:split_at], encoded_labels.iloc[split_at:]
    if train_labels.nunique() < len(OUTCOMES) or test_labels.nunique() < len(OUTCOMES):
        raise ValueError(
            "The chronological train/test split needs all three result classes "
            "in both partitions."
        )

    evaluation_model = _new_model()
    evaluation_model.fit(train_features, train_labels)
    test_probabilities = evaluation_model.predict_proba(test_features)
    predictions = test_probabilities.argmax(axis=1)
    metrics = {
        "accuracy": float(accuracy_score(test_labels, predictions)),
        "macro_f1": float(f1_score(
            test_labels,
            predictions,
            labels=list(range(len(OUTCOMES))),
            average="macro",
            zero_division=0,
        )),
        "log_loss": float(log_loss(
            test_labels,
            test_probabilities,
            labels=list(range(len(OUTCOMES))),
        )),
        "test_matches": float(len(test_labels)),
    }

    final_model = _new_model()
    final_model.fit(features, encoded_labels)
    return final_model, metrics, team_states, teams


def predict_match(
    model: Pipeline,
    home_team: str,
    away_team: str,
    team_states: dict[str, dict[str, Any]],
    teams: list[str],
) -> dict[str, Any]:
    """Return predicted result and probabilities for a future fixture."""
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
    home_elo = float(home_state.get("elo_rating", INITIAL_ELO))
    away_elo = float(away_state.get("elo_rating", INITIAL_ELO))
    features.update({
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": home_elo + HOME_ADVANTAGE_ELO - away_elo,
    })
    input_frame = pd.DataFrame([features])
    for column in TEAM_COLUMNS:
        input_frame[column] = pd.Categorical(input_frame[column], categories=teams)

    probabilities = model.predict_proba(input_frame)[0]
    outcome_probabilities = {
        OUTCOMES[index]: float(probability)
        for index, probability in enumerate(probabilities)
    }
    predicted_outcome = max(outcome_probabilities, key=outcome_probabilities.get)
    return {
        "outcome": predicted_outcome,
        "home_team": home_team,
        "away_team": away_team,
        "home_win_probability": outcome_probabilities["H"],
        "draw_probability": outcome_probabilities["D"],
        "away_win_probability": outcome_probabilities["A"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train an XGBoost model and optionally predict a fixture."
    )
    parser.add_argument("--home-team", help="Home team name for a fixture prediction.")
    parser.add_argument("--away-team", help="Away team name for a fixture prediction.")
    parser.add_argument(
        "--data",
        type=Path,
        default=DATA_PATH,
        help=f"CSV match data (default: {DATA_PATH.name}).",
    )
    parser.add_argument(
        "--model-path",
        type=Path,
        default=MODEL_PATH,
        help=f"Path for the trained model artifact (default: {MODEL_PATH.name}).",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for fixtures one at a time after training.",
    )
    args = parser.parse_args()
    if bool(args.home_team) != bool(args.away_team):
        parser.error("--home-team and --away-team must be provided together.")

    matches = pd.read_csv(args.data)
    model, metrics, team_states, teams = train_model(matches)
    args.model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": model, "team_states": team_states, "teams": teams},
        args.model_path,
    )

    if args.home_team and args.away_team:
        result = predict_match(
            model, args.home_team, args.away_team, team_states, teams
        )
        _print_prediction(result)
    else:
        print(f"Chronological holdout ({int(metrics['test_matches'])} matches):")
        print(f"  Accuracy: {metrics['accuracy']:.3f}")
        print(f"  Macro F1:  {metrics['macro_f1']:.3f}")
        print(f"  Log loss:  {metrics['log_loss']:.3f}")
        print(f"Final model saved to {args.model_path}")

    if not args.home_team and not args.away_team:
        _run_interactive(model, team_states, teams)


def _print_prediction(result: dict[str, Any]) -> None:
    if result["outcome"] == "H":
        most_likely = f"{result['home_team']} to win"
    elif result["outcome"] == "A":
        most_likely = f"{result['away_team']} to win"
    else:
        most_likely = "Draw"

    print(
        f"{result['home_team']} vs {result['away_team']}: "
        f"most likely outcome: {most_likely}"
    )
    print(f"  {result['home_team']} win: {result['home_win_probability']:.1%}")
    print(f"  Draw:              {result['draw_probability']:.1%}")
    print(f"  {result['away_team']} win: {result['away_win_probability']:.1%}")


def _run_interactive(
    model: Pipeline,
    team_states: dict[str, dict[str, Any]],
    teams: list[str],
) -> None:
    """Prompt for fixture teams repeatedly until the user exits."""
    print(
        "\nEnter two teams to predict their match. "
        "Team A is treated as the home team; press Enter at Team A to quit."
    )
    print(f"Teams: {', '.join(teams)}")
    while True:
        home_team = input("\nTeam A: ").strip()
        if not home_team:
            return
        away_team = input("Team B: ").strip()
        try:
            result = predict_match(model, home_team, away_team, team_states, teams)
        except ValueError as error:
            print(f"Could not predict fixture: {error}")
            continue
        _print_prediction(result)


if __name__ == "__main__":
    main()