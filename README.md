# Did Anyone Finish It?

IS630 Statistical Thinking in Data Science (G1), AY2026 Aug

Submission files (proposal, slides, report, declaration, code zip): https://drive.google.com/drive/folders/1iuUDbuXkfXNcnyEG2KQFCoV7JBL8h6j-?usp=sharing

```
IS630/
├── data/
│   ├── raw/                Kaggle archives, unmodified
│   ├── interim/            stage outputs, Parquet, one per notebook
│   ├── processed/          analysis-ready table for the modelling notebooks
│   └── external/
├── notebooks/              one notebook per stage, each loads the last stage's output
├── src/
│   └── is630/              shared code, imported by the notebooks
├── outputs/
│   ├── figures/            300 dpi, written from code
│   ├── tables/             csv and latex
│   └── models/             ArviZ traces, gitignored
```

## Section 1: Abstract

## Section 2: Problem, motivation and objectives

### 2a(i) Problem

A small studio interested in developing a game commits to a genre, a scope and a price range long before its release. However, it might have no way of knowing if players will like it until then.

### 2a(ii) Motivation

A small studio has less flexibility with poor selling games as larger studios do. As such, the value of understanding future performance is greater.

They may have limited budgets to run experiments or buy market research, so secondary data is the main evidence available. Public evidence that a studio could learn from such as Steam / Metacritic reviews, however, do not close that gap. These scores exist only when somebody chooses to review (selection bias), and are often percentages without absolute counts stated (sampling variability).

### 2a(iii) Objectives

1. Quantify how far critic scores track player reception, and identify where the two diverge.
2. Estimate player reception from the variables a studio controls, weighting each game by the number of reviews behind it
3. Define and compute a completion ratio from Steam playtime and HowLongToBeat completion times
4. Estimate completion from the same controllable variables

### 2b Analytical questions

1. What is a good metric for evaluating a game's success? We evaluate multiple possible metrics such as reviews, total playtime, completion rate.
2. Can we predict how successful a game will be? We study if, using the available data, we can build a model that holds some predictive power in predicting success.
3. What factors seem to be the most important for a game? We want to study if there are certain factors that are especially important that determine the success of a game, and highlight ones that a studio can control.
4. How do we translate these actionable insights into decisions that a business can make? For example, are there markets that are more important to user scores?
5. How does the number of player reviews affect the reliability of estimated player reception?

Notebooks map one to one: AQ1 `01_eda`, AQ2 `03_aq2_modelling`, AQ3 `04_aq3_factor_importance`, AQ4 `05_aq4_decisions`, AQ5 `06_aq5_review_reliability`. The study population is story-driven games matched to HowLongToBeat (notebook `00`). AQ2 and AQ3 regress the log completion ratio on game characteristics, with one frequentist and one Bayesian model each.

### 2c Context and novelty

[to insert relevant studies]

We propose the completion ratio as an alternative metric. Steam records how long the median owner played a game, HowLongToBeat records how long that game typically takes to finish, and neither source carries the ratio of the two. A ratio of 1.00 means the median player spent the typical number of hours a game takes to complete, and above 1.00 means they went past it.

Both datasets are well used on Kaggle, so the novelty is methodological rather than in the source. Partial pooling keeps low-visibility games in as weak evidence instead of filtering them out, and selection is treated as part of the question, including the match rate of the join itself.

Many games are open ended and thus have no set typical playtime (e.g. competitive games, sandbox games). The completion work is therefore restricted to story-driven games, and we report how many games that leaves.

## Section 3a: Dataset and variables

### 3a(i) Datasets

| | Steam | HowLongToBeat |
|---|---|---|
| Kaggle ref | `fronkongames/steam-games-dataset` | `b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset` |
| Rows | 125,855 published games | confirm on download |
| Size | 1.35 GB | 85 MB |
| Licence | MIT | MIT |
| Version used | v48, 11 Sep 2026 | v5, 29 Mar 2026 |
| Contributes | price, review counts, estimated playtime, critic score, genres, developers | main story, main plus sides and completionist hours, each with a poll count |

https://www.kaggle.com/datasets/fronkongames/steam-games-dataset https://www.kaggle.com/datasets/b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset

The Steam file covers published games only, with no DLC, episodes, music or videos. There is no shared identifier, so the join is on normalised title, with release year used to pick between candidates, and notebook `00` records the match rate.

Playtime and ownership come from SteamSpy rather than Valve. SteamSpy infers them from public Steam profiles, which are public by choice, so both are estimates from a self-selected sample rather than published counts.

### 3a(ii) Data dictionary

Column names confirmed against the downloaded files in `01_data_audit.ipynb`.

| Source | Field | Type | Description |
|---|---|---|---|
| Steam | `AppID`, `name`, `release_date` | id, text, date | identity and game age |
| Steam | `price` | numeric USD | price band, and a covariate throughout |
| Steam | `positive`, `negative` | counts | player reception and the sample size behind it |
| Steam | `recommendations` | count | store recommendations |
| Steam | `metacritic_score` | numeric 0 to 100 | critic reception |
| Steam | `median_playtime_forever`, `average_playtime_forever` | minutes | engagement, a SteamSpy estimate. Numerator of the completion ratio |
| Steam | `median_playtime_2weeks`, `average_playtime_2weeks` | minutes | retention signal |
| Steam | `estimated_owners` | bucketed range | audience size, a SteamSpy estimate |
| Steam | `peak_ccu` | count | concurrent audience |
| Steam | `genres`, `categories`, `tags` | lists | genre and mode |
| Steam | `developers`, `publishers` | lists | grouping for clustered errors and hierarchical models |
| Steam | `achievements`, `dlc_count`, `supported_languages` | counts, list | production scale proxies |
| Steam | `windows`, `mac`, `linux` | bool | platform support |
| Steam | `required_age` | numeric | audience age band |
| HLTB | `id`, `name`, `release_date`, `release_year` | id, text, date | join keys |
| HLTB | `type` | categorical | filter to `game`, excluding DLC and expansions |
| HLTB | `main_story`, `main_story_polled` | hours, count | denominator of the completion ratio, with its sample size |
| HLTB | `main_plus_sides`, `completionist` and poll counts | hours, count | scope bands and the completionist gap |
| HLTB | `genres`, `platform` | lists | cross-check against Steam genres |

