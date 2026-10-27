"""Completion-ratio model setup shared by notebooks 03 (AQ2) and 04 (AQ3), so both
read the same sample, the same standardisation and the same Bayesian model."""

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pymc as pm

from . import config
from .features import extract_primary_developer

# Prior SDs on standardised predictors, stated and justified in notebook 03, section 3.
COMPLETION_PRIORS = {"intercept": 1.0, "beta": 0.5, "sigma_dev": 0.5, "sigma": 1.0, "tau": 1.0}
SAMPLE_KW = dict(draws=1000, tune=1000, chains=4, target_accept=0.9, nuts_sampler="numpyro",
                 random_seed=config.SEED, progressbar=False)


def completion_sample(df_train: pd.DataFrame, df_val: pd.DataFrame, features: list) -> SimpleNamespace:
    """Completion-model rows with the log target, developer groups, and design matrices
    whose continuous columns are standardised on development-training statistics."""
    train = df_train[df_train["flag_completion_model"]].copy()
    val = df_val[df_val["flag_completion_model"]].copy()
    for frame in (train, val):
        frame["log_ratio"] = np.log(frame["completion_ratio"])
        if "developer_group" not in frame:
            frame["developer_group"] = extract_primary_developer(frame["steam_developers"], frame["steam_appid"])
    assert np.isfinite(train["log_ratio"]).all() and np.isfinite(val["log_ratio"]).all()

    binary = [f for f in features if set(pd.unique(train[f].dropna())) <= {0, 1}]
    continuous = [f for f in features if f not in binary]
    centre, scale = train[continuous].mean(), train[continuous].std()
    assert scale.gt(0).all()

    def design(frame):
        X = frame[features].astype(float).copy()
        X[continuous] = (X[continuous] - centre) / scale
        return X

    dev_levels = train["developer_group"].value_counts().index.to_numpy()
    dev_index = {d: i for i, d in enumerate(dev_levels)}
    return SimpleNamespace(
        train=train, val=val, X_train=design(train), X_val=design(val), design=design,
        y_train=train["log_ratio"].to_numpy(), y_val=val["log_ratio"].to_numpy(),
        binary=binary, continuous=continuous, centre=centre, scale=scale,
        dev_levels=dev_levels,
        dev_train=train["developer_group"].map(dev_index).to_numpy(),
        # A validation developer not seen in training gets -1, meaning the population average.
        dev_val=val["developer_group"].map(dev_index).fillna(-1).astype(int).to_numpy(),
        inv_polls_train=1.0 / train["hltb_main_story_polled"].to_numpy(dtype=float),
        inv_polls_val=1.0 / val["hltb_main_story_polled"].to_numpy(dtype=float),
    )


def completion_model(X: pd.DataFrame, y, dev, inv_polls, n_dev: int, priors: dict) -> pm.Model:
    """Hierarchical normal regression on the log ratio with developer intercepts and
    noise sqrt(sigma^2 + tau^2 / polls). Priors are SDs keyed by parameter name."""
    coords = {"feature": list(X.columns), "developer": np.arange(n_dev)}
    with pm.Model(coords=coords) as model:
        X_data = pm.Data("X", X.to_numpy())
        dev_data = pm.Data("dev", dev)
        inv_polls_data = pm.Data("inv_polls", inv_polls)
        intercept = pm.Normal("intercept", 0, priors["intercept"])
        beta = pm.Normal("beta", 0, priors["beta"], dims="feature")
        sigma_dev = pm.HalfNormal("sigma_dev", priors["sigma_dev"])
        z_dev = pm.Normal("z_dev", 0, 1, dims="developer")
        sigma = pm.HalfNormal("sigma", priors["sigma"])
        tau = pm.HalfNormal("tau", priors["tau"])
        mu = intercept + X_data @ beta + sigma_dev * z_dev[dev_data]
        noise = pm.math.sqrt(sigma ** 2 + tau ** 2 * inv_polls_data)
        pm.Normal("log_ratio", mu, noise, observed=y, shape=X_data.shape[0])
    return model
