# Data Relation

This directory contains derived analytical datasets, statistical profiles, and the analysis notebook generated from the Premier League dataset (`combined_data.csv`).

---

## Directory Contents

| File | Description |
| :--- | :--- |
| `data_check.ipynb` | Jupyter Notebook containing data checks, exploratory analyses, baseline statistics, tactical profiling logic, and dataset generation code. |
| `ref_cards.csv` | Summary of referee disciplinary statistics (yellow/red card rates and league baseline deviations). |
| `team_home_away_profiles.csv` | Historical win/draw/loss percentages and match counts for each team split by Home and Away fixtures. |
| `team_attack_or_defense_type.csv` | Team classifications (Attack vs. Defense) and relative scoring/conceding performance relative to league averages. |

---

## Value & Naming Dictionary

### 1. Match & Card Abbreviations
* **`n` / `n_home` / `n_away`**: Sample size (number of matches recorded).
* **`FTR`**: Full Time Result (`H` = Home Win, `D` = Draw, `A` = Away Win).
* **`HY` / `AY`**: Home / Away Team Yellow Cards.
* **`HR` / `AR`**: Home / Away Team Red Cards.
* **`FTHG` / `FTAG`**: Full Time Home / Away Team Goals scored.
* **`yellow_gap`**: Referee yellow card rate relative to the league average (`yellows_per_game - league_avg`). Positive indicates stricter than average; negative indicates more lenient.
* **`red_gap`**: Referee red card rate relative to the league average (`reds_per_game - league_avg`). Positive indicates stricter than average; negative indicates more lenient.

### 2. Result Profile Values (`team_home_away_profiles.csv`)
* **`win_pct_home` / `win_pct_away`**: Percentage of matches won at home / away.
* **`draw_pct_home` / `draw_pct_away`**: Percentage of matches ending in a draw at home / away.
* **`lose_pct_home` / `lose_pct_away`**: Percentage of matches lost at home / away.

### 3. Tactical Archetypes & Metric Values (`team_attack_or_defense_type.csv`)
* **Tactical Categories (`overall_type`, `home_type`, `away_type`)**:
  * **`Strong Attack & Defense`**: Above-average offensive scoring and below-average goals conceded (elite performance on both ends).
  * **`Attack Team`**: Above-average goal scoring performance relative to the league.
  * **`Defense Team`**: Concedes fewer goals than the league average (strong defensive discipline).
  * **`Weak Both`**: Below-average goal scoring and above-average goals conceded.
* **Relative Shift Values (`home_attack%`, `home_defense%`, `away_attack%`, `away_defense%`)**:
  * **`Attack %` (`+` / `-`)**: Percentage difference compared to league scoring baseline. (`+` = scores more than average, `-` = scores fewer than average).
  * **`Defense %` (`+` / `-`)**: Percentage difference compared to league goal-conceding baseline. (`-` = concedes fewer than average / better defense, `+` = concedes more than average / weaker defense).

---

## Methodology & Calculations

### 1. Referee Card Rates (`ref_cards.csv`)
* $\text{Total Yellows} = \text{HY} + \text{AY}$
* $\text{Total Reds} = \text{HR} + \text{AR}$
* $\text{yellows\_per\_game} = \frac{\text{total\_yellow}}{n}$
* $\text{reds\_per\_game} = \frac{\text{total\_red}}{n}$
* $\text{yellow\_gap} = \text{yellows\_per\_game} - \text{league\_yellow\_avg}$
* $\text{red\_gap} = \text{reds\_per\_game} - \text{league\_red\_avg}$

### 2. Team Tactical Strength Ratios (`team_attack_or_defense_type.csv`)

#### Baseline Goal Averages:
* **League Avg Home Goals (`league_home_goals_avg`)**: $\approx 1.445$
* **League Avg Away Goals (`league_away_goals_avg`)**: $\approx 1.312$

#### Strength Formulas:
* $\text{home\_attack\_val} = \frac{\text{Team Home Goals Scored Avg}}{\text{league\_home\_goals\_avg}}$
* $\text{home\_defense\_val} = \frac{\text{Team Home Goals Conceded Avg}}{\text{league\_away\_goals\_avg}}$
* $\text{away\_attack\_val} = \frac{\text{Team Away Goals Scored Avg}}{\text{league\_away\_goals\_avg}}$
* $\text{away\_defense\_val} = \frac{\text{Team Away Goals Conceded Avg}}{\text{league\_home\_goals\_avg}}$

#### Overall Power Index:
* $\text{Average Attack Power} = \frac{\text{home\_attack\_val} + \text{away\_attack\_val}}{2}$
* $\text{Average Defense Power} = 2.0 - \left(\frac{\text{home\_defense\_val} + \text{away\_defense\_val}}{2}\right)$
* Classified as **`Attack Team`** if $\text{Attack Power} \ge \text{Defense Power}$, otherwise **`Defense Team`**.
