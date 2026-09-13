# CLAUDE.md

Guidance for Claude Code sessions in this repository.

## What this is

An IS630 (Statistical Thinking in Data Science, SMU, AY2026 Aug) group project
worth 30% of the grade. It joins two Kaggle datasets, Steam store data
(`fronkongames/steam-games-dataset`, 1.35 GB, MIT) and HowLongToBeat completion
times (`b4n4n4p0wer/how-long-to-beat-video-game-playtime-dataset`, 85 MB, MIT),
from the perspective of a small independent studio shipping PC-first on Steam
and deciding what to build next.

The project moved off the RAWG dataset on 13 Sep 2026, before any code was
written. If you find a reference to RAWG, `added_by_status` or a 7.31 GB
download anywhere in this repo, it is stale, so fix it.

Read `README.md` first. It holds the project brief (stakeholder, problem,
objectives, the three analytical questions), the dataset summary and the file
layout. Do not restate them here. The README is the single place the brief
lives, so keep it current and do not spin off parallel draft documents.

## Hard rules

- **Never commit or push unless the user explicitly asks.** Stage nothing on
  your own. This one is not negotiable.
- **Never commit data.** `data/` is gitignored. The two raw downloads are about
  1.4 GB together.
- **Never write interpretations, recommendations or final analytical questions
  into the deliverables.** The course brief prohibits GenAI for framing the
  final analytical questions, interpreting results, evaluating model
  performance, and making recommendations. You may write code, produce tables
  and figures, restructure documents, and draft non-interpretive prose. When a
  task crosses that line, say so and stop, and leave a clearly marked
  placeholder for the student.
- **No literature review.** The brief bans general-purpose GenAI for it and
  allows only SMU Library tools (Research Assistant, Scopus AI, Scite,
  SciSpace). Do not produce citations from memory. Never invent a reference.
- Anything drafted with your help has to be declarable in `docs/declaration/`.
  If you produce something substantial, mention that it needs declaring.

## Stack

Python with pandas and pyarrow, scipy, statsmodels and pingouin for frequentist
work, PyMC and ArviZ for Bayesian work, matplotlib and seaborn for figures.
See `requirements.txt`. Jupyter notebooks under `notebooks/`, shared code under
`src/is630/`.

Environment is Windows. Use forward slashes in Python paths via `pathlib`, and
remember the shell here is PowerShell by default.

## Working conventions

- Notebooks are numbered and run in order. Each one must execute top to bottom
  on a fresh kernel. Do not leave a notebook whose cells only work out of order.
- Logic used by more than one notebook belongs in `src/is630`, imported, not
  copy-pasted. If you find duplicated cleaning logic across notebooks, move it.
- Never hardcode a path. Everything comes from `src/is630/config.py`.
- One random seed, in `config.py`, imported everywhere.
- Reading the Steam file: pass an explicit column list. The free-text and URL
  columns (`about_the_game`, `detailed_description`, `screenshots`, `movies`,
  `header_image`, `website`, `support_url` and similar) are most of the bulk and
  none of them are needed. Confirm the real column names in notebook `01` before
  relying on them.
- The Steam dataset refreshes continuously. Never re-download mid-project. The
  archive in `data/raw` plus the version number recorded in notebook `00` is the
  pin, and the proposal and the report must come off the same one.
- Intermediate data is Parquet, not CSV. Only the final submission table is CSV.
- Figures save to `outputs/figures` at 300 dpi with a named file, from code.
  Tables save to `outputs/tables`.

## Statistical standards

These exist because the rubric marks understanding of statistical concepts, and
because it is easy to produce a plausible-looking wrong answer here.

- Report effect sizes with every test, not just p-values.
- Correct for multiple comparisons (Benjamini-Hochberg) when testing many
  genres, platforms or tags at once.
- Games from the same publisher or developer are not independent. Cluster
  standard errors, or use a hierarchical model.
- `positive`, `negative`, `recommendations`, `estimated_owners` and the
  `_forever` playtime columns all accumulate with a game's age. Control for
  `years_since_release` or normalise by it. Do not compare raw counts across
  release years.
- `metacritic_score` is missing not at random. Any analysis conditioning on it
  describes reviewed games only. Say so in the output, do not impute it.
- `estimated_owners` is a bucketed SteamSpy model output, not a measured count.
  Treat it as interval-censored and say where the interval came from. The
  SteamSpy playtime columns are inferred from public Steam profiles, so they are
  estimates from a self-selected sample. Never call either one measured.
- `price` is the price at scrape time, not the launch price. Games are repriced
  and permanently discounted, so price answers what games at that point look
  like now, not what a studio should charge at launch. Say so wherever price
  carries a conclusion.
- "Story-driven" is not a field. Build it in notebook `02` from Steam
  `categories` and `tags` plus HLTB `type`, write the rule down, and report how
  many games it keeps. It is a design choice a marker can question.
- The completion ratio has asymmetric uncertainty. `main_story_polled` gives the
  exact count behind the denominator, but the numerator has only a bucketed
  owner range, with no count of the profiles behind the playtime median. Model
  the denominator's uncertainty properly and state that the numerator's cannot
  be.
- The Steam to HowLongToBeat join is on normalised title plus release year, so
  it matches a biased subset. Report the match rate, and compare matched against
  unmatched rows on the variables you do have before drawing conclusions from
  the matched set.
- The completion ratio has a sample size on both sides. Weight or model the HLTB
  denominator by its `*_polled` count rather than treating a two-person poll and
  a two-thousand-person poll as equal evidence.
- For every PyMC model, report R-hat, effective sample size, divergence count
  and a posterior predictive check. A model that diverged is not a result.
- State priors explicitly and run a sensitivity check.
- Do not let inclusion thresholds drift after seeing outcomes. They are set in
  notebook `02` and recorded there.

## Deliverables and page limits

Set by the course brief, do not exceed them:

| Deliverable | Limit | Weight |
|---|---|---|
| Proposal | 4 pages, excluding cover and references | 5% |
| Presentation | 17 slides, 15 minutes | 10% group + 5% individual |
| Report | 10 A4 pages, font 11, excluding references | 10% with code base |
| Medium article (alternative) | 15 minute read | same |

Drafts live under `docs/`. Final submissions are uploaded to the shared Drive
folder linked in `README.md`.

## Markdown formatting

Do not hard-wrap prose. One paragraph is one line, one list item is one line,
however long it runs. Wrapping belongs to the editor, not the file. Code fences,
tables and `$$` math blocks keep their own line structure.

## Writing style for any prose you draft

The brief warns that over-reliance on GenAI is detectable and penalised. Keep
drafts plain: no "delve", "crucial", "underscores", "landscape", "showcase", no
em dashes, no three-item lists by reflex, no closing lines that restate the
paragraph above. Short sentences. Write what the number says and stop.
