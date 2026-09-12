# Did Anyone Finish It?

IS630 Statistical Thinking in Data Science (G1), AY2026 Aug

Submission files (proposal, slides, report, declaration, code zip):
https://drive.google.com/drive/folders/1iuUDbuXkfXNcnyEG2KQFCoV7JBL8h6j-?usp=sharing

```
IS630/
├── data/                   
│   ├── raw/                Kaggle archives, unmodified
│   ├── interim/            column-pruned Parquet
│   ├── processed/          joined, analysis-ready tables
│   └── external/
├── notebooks/              
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

A small studio interested in developing a game commits to a genre, a scope and a price range long before its release. However, it has no way of knowing if players will like it until its release.

They may have limited budgets to run experiments or buy market research, so secondary data is the main evidence available. Public evidence that a studio could learn from such as Steam / Metacritic reviews, however, do not close that gap. These scores exist only when somebody chooses to review (selection bias), and are often percentages without absolute counts stated (sampling variability).

### 2a(ii) Motivation

We want to study the population of games released on Steam to see if a studio can learn from those insights to deliver a well received game. 

We propose a new metric beyond pure review rating - completion rate based on typical game time. A 1.00 completion rate indicates that the median player spent the typical number of hours a game takes to complete. We believe that this is a good metric that reduces the impact of game popularity.

This presents an issue in that many games are open ended and thus have no set typical playtime (e.g. competitive games, sandbox games). We focus primarily on story-driven games in this case.

### 2a(iii) Objectives



### 2b Analytical questions



### 2c Context and novelty

Both datasets are well used on Kaggle, so the novelty is methodological rather
than in the source: the join produces a completion measure that neither file
carries, and partial pooling keeps low-visibility games in as weak evidence
instead of filtering them out. Selection is treated as part of the question,
including the match rate of the join itself.

## Section 3a: Dataset and variables

### 3a(i) Datasets

| | Steam | HowLongToBeat |
|---|---|---|
| Kaggle ref | `fronkongames/steam-games-dataset` | `b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset` |
| Rows | 125,855 published games | confirm on download |
| Size | 1.35 GB | 85 MB |
| Licence | MIT | MIT |
| Version used | v48, 11 Sep 2026 | v5, 29 Mar 2026 |
| Contributes | price, review counts, measured playtime, critic score, genres, developers | main story, main plus sides and completionist hours, each with a poll count |

https://www.kaggle.com/datasets/fronkongames/steam-games-dataset
https://www.kaggle.com/datasets/b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset

The Steam file covers published games only, with no DLC, episodes, music or
videos. There is no shared identifier, so the join is on normalised title plus
release year and notebook `02` records the match rate.

### 3a(ii) Data dictionary

Column names confirmed against the downloaded files in `01_data_audit.ipynb`.

| Source | Field | Type | Description |
|---|---|---|---|
| Steam | `AppID`, `name`, `release_date` | id, text, date | identity and game age |
| Steam | `price` | numeric USD | price band, and a covariate throughout |
| Steam | `positive`, `negative` | counts | player reception and the sample size behind it |
| Steam | `recommendations` | count | store recommendations |
| Steam | `metacritic_score` | numeric 0 to 100 | critic reception |
| Steam | `median_playtime_forever`, `average_playtime_forever` | minutes | measured engagement, numerator of the completion ratio |
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

## Getting started

```bash
python -m venv .venv && .venv/Scripts/activate && pip install -r requirements.txt
```

Put your Kaggle API token at `~/.kaggle/kaggle.json` and run
`notebooks/00_setup_and_acquisition.ipynb`. Keep the downloaded archives in
`data/raw` unmodified, because the Steam dataset refreshes continuously and the
proposal and report must come off the same version.
