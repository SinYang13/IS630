# Green Light for an Indie Studio

IS630 Statistical Thinking in Data Science (G1), AY2026 Aug

## Abstract

Small game studios must make important decisions before knowing how players will respond. This project investigates if publicly available game data can provide insights to support these decisions. We combine Steam game data with HowLongToBeat (HLTB) playtime data to examine player reception and engagement. We propose the completion ratio by comparing median Steam playtime with estimated completion time provided by HLTB as an alternative. We model the completion ratio using OLS and Bayesian Hierarchical Regression, showing that there is some, albeit limited, evidence that completion ratio can be modelled. The top variables show that having achievements and being in early access are among the key drivers in completion ratio. Businesses interested in these insights can prioritise these factors, although we caution that these insights are based only on correlation, not causation. We then evaluate the ability for us to tell apart games by their positive review rate. We show in practice how games with different positive review rates can be statistically indifferent. We refit the final model on all 3,081 eligible games for use in future prediction. However, the predictive use of the model is limited by a lack of outcome data and bias introduced during analysis.

## Project

| Notebook | Stage |
|---|---|
| `00_setup_and_acquisition` | Join the datasets, scope to story-driven games, split train and test |
| `01_eda` | EDA and AQ1: What metrics define success? |
| `02_cleaning_and_features` | Cleaning, features and inclusion thresholds |
| `03_aq2_modelling` | AQ2: Can success be modelled? |
| `04_aq3_factor_importance` | AQ3: What factors can we control? |
| `05_aq4_decisions` | AQ4: What insights can we draw? |
| `06_aq5_review_reliability` | AQ5: How does number of reviews affect scores? |
| `07_final_test_scoring` | Final test score and refit |

Data: [Steam](https://www.kaggle.com/datasets/fronkongames/steam-games-dataset) (v49) and [HowLongToBeat](https://www.kaggle.com/datasets/b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset) (v5), both from Kaggle, pulled 19 Sep 2026. `data/` is gitignored.

Submission files: https://drive.google.com/drive/folders/1iuUDbuXkfXNcnyEG2KQFCoV7JBL8h6j-?usp=sharing
