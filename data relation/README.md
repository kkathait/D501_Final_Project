# Data Relation

This directory contains derived analytical datasets, statistical profiles, and the exploratory analysis notebook generated from the Premier League dataset (`combined_data.csv`).

---

## Directory Contents

| File | Description |
| :--- | :--- |
| `data_check.ipynb` | Jupyter Notebook containing data checks, exploratory analyses, baseline statistics, tactical profiling logic, and dataset generation code. |
| `combine csv stats relation.xlsx` | Excel workbook containing consolidated statistical cross-references, summary sheets, and relational tables. |
| `ref_cards.csv` | Summary of referee disciplinary statistics (yellow/red card rates and league baseline deviations). |
| `team_home_away_profiles.csv` | Historical win/draw/loss percentages and match counts for each team split by Home and Away fixtures. |
| `team_attack_or_defense_type.csv` | Team tactical classifications (Attack vs. Defense) and relative scoring/conceding performance relative to league averages. |

---

## Value & Naming Dictionary

### 1. Match & Card Abbreviations
* **`n` / `n_home` / `n_away`**: Sample size (number of matches recorded).
* **`FTR`**: Full Time Result (`H` = Home Win, `D` = Draw, `A` = Away Win).
* **`HY` / `AY`**: Home / Away Team Yellow Cards.
* **`HR` / `AR`**: Home / Away Team Red Cards.
* **`FTHG` / `FTAG`**: Full Time Home / Away Team Goals scored.
* **`yellow_gap`**: Referee yellow card rate relative to the league average (`yellows_per_game - league_yellow_avg`). Positive values indicate stricter refereeing than average; negative values indicate more lenient.
* **`red_gap`**: Referee red card rate relative to the league average (`reds_per_game - league_red_avg`). Positive values indicate stricter refereeing than average; negative values indicate more lenient.

### 2. Result Profile Values (`team_home_away_profiles.csv`)
* **`win_pct_home` / `win_pct_away`**: Percentage of matches won at home / away.
* **`draw_pct_home` / `draw_pct_away`**: Percentage of matches ending in a draw at home / away.
* **`lose_pct_home` / `lose_pct_away`**: Percentage of matches lost at home / away.

### 3. Tactical Archetypes & Metric Values (`team_attack_or_defense_type.csv`)
* **Tactical Categories (`overall_type`, `home_type`, `away_type`)**:
  * **`Strong Attack & Defense`**: Above-average offensive scoring (>= 1.0) and below-average goals conceded (<= 1.0).
  * **`Attack Team`**: Above-average goal scoring performance relative to league average (>= 1.0).
  * **`Defense Team`**: Concedes fewer goals than league average (< 1.0).
  * **`Weak Both`**: Below-average goal scoring and above-average goals conceded.
* **Relative Shift Values (`home_attack%`, `home_defense%`, `away_attack%`, `away_defense%`)**:
  * **`Attack %` (`+` / `-`)**: Percentage difference compared to league scoring baseline (`(val - 1.0) * 100%`). (`+` = scores more than average, `-` = scores fewer than average).
  * **`Defense %` (`+` / `-`)**: Percentage difference compared to league goal-conceding baseline (`(val - 1.0) * 100%`). (`-` = concedes fewer than average / better defense, `+` = concedes more than average / weaker defense).

---

## Methodology & Calculations

### 1. Referee Card Rates (`ref_cards.csv`)

* **Total Yellow Cards**:
  `Total Yellows = HY + AY`

* **Total Red Cards**:
  `Total Reds = HR + AR`

* **Yellows per Game**:
  `yellows_per_game = total_yellow / n`

* **Reds per Game**:
  `reds_per_game = total_red / n`

* **Yellow Gap (vs. League Average)**:
  `yellow_gap = yellows_per_game - league_yellow_avg`

* **Red Gap (vs. League Average)**:
  `red_gap = reds_per_game - league_red_avg`

---

### 2. Team Tactical Strength Ratios (`team_attack_or_defense_type.csv`)

#### Baseline Goal Averages:
* **League Avg Home Goals (`league_home_goals_avg`)**: ≈ 1.445
* **League Avg Away Goals (`league_away_goals_avg`)**: ≈ 1.312

#### Strength Formulas:
* **Home Attack Ratio**:
  `home_attack_val = Team Home Goals Scored Avg / league_home_goals_avg`

* **Home Defense Ratio**:
  `home_defense_val = Team Home Goals Conceded Avg / league_away_goals_avg`

* **Away Attack Ratio**:
  `away_attack_val = Team Away Goals Scored Avg / league_away_goals_avg`

* **Away Defense Ratio**:
  `away_defense_val = Team Away Goals Conceded Avg / league_home_goals_avg`

#### Overall Power Index & Classification:
* **Average Attack Power**:
  `Average Attack Power = (home_attack_val + away_attack_val) / 2`

* **Average Defense Power**:
  `Average Defense Power = 2.0 - ((home_defense_val + away_defense_val) / 2)`

* **Overall Classification**:
  * Classified as **`Attack Team`** if `Average Attack Power >= Average Defense Power`
  * Otherwise classified as **`Defense Team`**
