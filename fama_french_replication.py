import io
import zipfile
import os

import numpy as np
import pandas as pd
import requests
import statsmodels.api as sm
from scipy import stats

FACTORS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
PORTFOLIOS_URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/25_Portfolios_5x5_CSV.zip"

SPLIT_DATE = "2000-01-01"


def download_and_extract_csv(url: str) -> str:
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        inner_name = z.namelist()[0]
        with z.open(inner_name) as f:
            raw_bytes = f.read()
    return raw_bytes.decode("latin-1")


def parse_ff_monthly_block(raw_text: str, block_label: str = None, date_len: int = 6) -> pd.DataFrame:
    lines = raw_text.splitlines()

    start_scan = 0
    if block_label is not None:
        for i, line in enumerate(lines):
            if block_label in line:
                start_scan = i + 1
                break
        else:
            raise ValueError(f"Block label '{block_label}' not found in file")

    header_idx = None
    for i in range(start_scan, len(lines)):
        if lines[i].startswith(","):
            header_idx = i
            break
    if header_idx is None:
        raise ValueError("Could not locate header row")

    header = lines[header_idx].split(",")
    col_names = ["date"] + [c.strip() for c in header[1:] if c.strip() != ""]

    data_rows = []
    for line in lines[header_idx + 1:]:
        if not line.strip():
            break
        first_field = line.split(",")[0].strip()
        if first_field.lstrip("-").isdigit() and len(first_field.lstrip("-")) == date_len:
            data_rows.append(line)
        else:
            break

    csv_block = "\n".join([",".join(col_names)] + data_rows)
    df = pd.read_csv(io.StringIO(csv_block))
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m")
    df = df.set_index("date")
    df = df.apply(pd.to_numeric, errors="coerce")

    df = df.replace([-99.99, -999, -999.0], np.nan)

    df = df / 100.0
    return df


def load_data():
    factors_raw = download_and_extract_csv(FACTORS_URL)
    factors = parse_ff_monthly_block(factors_raw)

    ports_raw = download_and_extract_csv(PORTFOLIOS_URL)
    portfolios = parse_ff_monthly_block(
        ports_raw, block_label="Average Value Weighted Returns -- Monthly"
    )
    return factors, portfolios


def build_excess_return_panel(factors: pd.DataFrame, portfolios: pd.DataFrame):
    merged = portfolios.join(factors[["RF"]], how="inner")
    port_cols = [c for c in portfolios.columns]
    excess = merged[port_cols].sub(merged["RF"], axis=0)
    return excess, factors.loc[merged.index]


def run_ff3_regression(y: pd.Series, factors: pd.DataFrame) -> dict:
    X = sm.add_constant(factors[["Mkt-RF", "SMB", "HML"]], has_constant="add")
    model = sm.OLS(y, X, missing="drop").fit()
    return {
        "alpha": model.params["const"],
        "alpha_t": model.tvalues["const"],
        "alpha_p": model.pvalues["const"],
        "beta_mkt": model.params["Mkt-RF"],
        "beta_smb": model.params["SMB"],
        "beta_hml": model.params["HML"],
        "r2": model.rsquared,
        "n_obs": int(model.nobs),
    }


def run_all_portfolios(excess_panel: pd.DataFrame, factors: pd.DataFrame) -> pd.DataFrame:
    results = {}
    for col in excess_panel.columns:
        results[col] = run_ff3_regression(excess_panel[col], factors)
    return pd.DataFrame(results).T


def factor_premium_decay_test(factors: pd.DataFrame, split_date: str):
    pre = factors.loc[factors.index < split_date]
    post = factors.loc[factors.index >= split_date]

    out = {}
    for factor in ["SMB", "HML"]:
        t_stat, p_val = stats.ttest_ind(pre[factor], post[factor], equal_var=False)
        out[factor] = {
            "mean_pre": pre[factor].mean(),
            "mean_post": post[factor].mean(),
            "annualized_pre_%": pre[factor].mean() * 12 * 100,
            "annualized_post_%": post[factor].mean() * 12 * 100,
            "welch_t": t_stat,
            "p_value": p_val,
        }
    return pd.DataFrame(out).T

def model_fit_comparison(excess_panel: pd.DataFrame, factors: pd.DataFrame, split_date: str):
    pre_mask = excess_panel.index < split_date
    post_mask = excess_panel.index >= split_date

    pre_results = run_all_portfolios(excess_panel.loc[pre_mask], factors.loc[pre_mask])
    post_results = run_all_portfolios(excess_panel.loc[post_mask], factors.loc[post_mask])

    summary = pd.DataFrame({
        "avg_abs_alpha_pre_%": [pre_results["alpha"].abs().mean() * 100],
        "avg_abs_alpha_post_%": [post_results["alpha"].abs().mean() * 100],
        "pct_significant_alpha_pre": [(pre_results["alpha_p"] < 0.05).mean()],
        "pct_significant_alpha_post": [(post_results["alpha_p"] < 0.05).mean()],
        "avg_r2_pre": [pre_results["r2"].mean()],
        "avg_r2_post": [post_results["r2"].mean()],
    })
    return summary, pre_results, post_results

def main():
    os.makedirs("output", exist_ok=True)
    print("Downloading data from Ken French's Data Library...")
    factors, portfolios = load_data()
    print(f"Factors: {len(factors)} months, {factors.index.min().date()} to {factors.index.max().date()}")
    print(f"Portfolios: {len(portfolios)} months, {portfolios.shape[1]} portfolios")

    excess_panel, factors_aligned = build_excess_return_panel(factors, portfolios)

    print("\n=== Full-sample regression results (all 25 portfolios) ===")
    full_results = run_all_portfolios(excess_panel, factors_aligned)
    print(full_results.round(4))
    full_results.to_csv("output/full_sample_results.csv")

    print(f"\n=== Factor premium decay test (split at {SPLIT_DATE}) ===")
    premium_test = factor_premium_decay_test(factors_aligned, SPLIT_DATE)
    print(premium_test.round(4))
    premium_test.to_csv("output/factor_premium_decay.csv")

    print(f"\n=== Model fit comparison (split at {SPLIT_DATE}) ===")
    fit_summary, pre_results, post_results = model_fit_comparison(excess_panel, factors_aligned, SPLIT_DATE)
    print(fit_summary.round(4))
    fit_summary.to_csv("output/fit_comparison_summary.csv")
    pre_results.to_csv("output/pre_2000_results.csv")
    post_results.to_csv("output/post_2000_results.csv")

    print("\nDone. Results saved to output/")


if __name__ == "__main__":
    main()
