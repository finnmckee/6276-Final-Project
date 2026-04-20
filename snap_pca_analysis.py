import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA


file_path = "MMG2024_2019-2022_Data_ToShare_v3.xlsx"
sheet_name = "County"

df = pd.read_excel(file_path, sheet_name=sheet_name)


df["State"] = df["State"].astype(str).str.strip()
df = df[(df["State"] == "NC") & (df["Year"] == 2022)].copy()

print("Rows after filtering:", len(df))
print("States present:", df["State"].unique())


pca_vars = [
    "Overall Food Insecurity Rate",
    "Child Food Insecurity Rate",
    "Cost Per Meal",
    "% FI > SNAP Threshold"
]

keep_cols = ["County, State", "FIPS", "State", "Year"] + pca_vars
df = df[keep_cols].copy()

for col in pca_vars:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df = df.dropna(subset=pca_vars).copy()


scaler = StandardScaler()
X_scaled = scaler.fit_transform(df[pca_vars])


pca = PCA(n_components=2)
pcs = pca.fit_transform(X_scaled)

df["PC1_raw"] = pcs[:, 0]
df["PC2_raw"] = pcs[:, 1]

loadings = pd.DataFrame(
    pca.components_.T,
    index=pca_vars,
    columns=["PC1", "PC2"]
)


if np.corrcoef(df["PC1_raw"], df["Overall Food Insecurity Rate"])[0, 1] < 0:
    df["PC1"] = -df["PC1_raw"]
    loadings["PC1"] = -loadings["PC1"]
else:
    df["PC1"] = df["PC1_raw"]

if np.corrcoef(df["PC2_raw"], df["% FI > SNAP Threshold"])[0, 1] < 0:
    df["PC2"] = -df["PC2_raw"]
    loadings["PC2"] = -loadings["PC2"]
else:
    df["PC2"] = df["PC2_raw"]

print("\n=== PCA LOADINGS ===")
print(loadings.round(6))

print("\n=== EXPLAINED VARIANCE ===")
for i, ratio in enumerate(pca.explained_variance_ratio_, start=1):
    print(f"PC{i}: {ratio:.4f}")


fixed_scenarios = {
    "Need_80_20": (0.80, 0.20),
    "Need_70_30": (0.70, 0.30),
    "Need_60_40": (0.60, 0.40),
    "Balanced_50_50": (0.50, 0.50),
    "Access_30_70": (0.30, 0.70),
}

scenario_rows = []

for scenario_name, (w1, w2) in fixed_scenarios.items():
    df[scenario_name] = w1 * df["PC1"] + w2 * df["PC2"]
    corr = np.corrcoef(df[scenario_name], df["Overall Food Insecurity Rate"])[0, 1]
    top10 = df.nlargest(10, scenario_name)

    scenario_rows.append({
        "Scenario": scenario_name,
        "PC1_weight": w1,
        "PC2_weight": w2,
        "Correlation_with_FI": corr,
        "Top10_Avg_FI": top10["Overall Food Insecurity Rate"].mean()
    })

scenario_summary = pd.DataFrame(scenario_rows).sort_values(
    "Correlation_with_FI", ascending=False
).reset_index(drop=True)

print("\n=== FIXED SCENARIO RESULTS (REFERENCE ONLY) ===")
print(scenario_summary.round(6))


ratio_rows = []

for w1 in range(100, -1, -10):
    w2 = 100 - w1
    col_name = f"Ratio_{w1}_{w2}"

    df[col_name] = (w1 / 100.0) * df["PC1"] + (w2 / 100.0) * df["PC2"]

    corr = np.corrcoef(df[col_name], df["Overall Food Insecurity Rate"])[0, 1]
    top10 = df.nlargest(10, col_name)

    ratio_rows.append({
        "PC1_weight": w1,
        "PC2_weight": w2,
        "Scenario": f"{w1}/{w2}",
        "Correlation_with_FI": corr,
        "Top10_Avg_FI": top10["Overall Food Insecurity Rate"].mean()
    })

ratio_summary = pd.DataFrame(ratio_rows).sort_values(
    "PC1_weight", ascending=False
).reset_index(drop=True)

print("\n=== FULL RATIO SENSITIVITY RESULTS ===")
print(ratio_summary.round(6))


STRATEGIC_W1 = 70
STRATEGIC_W2 = 30
strategic_col = f"Ratio_{STRATEGIC_W1}_{STRATEGIC_W2}"

print("\n=== STRATEGIC RATIO SELECTED ===")
print(f"Using {STRATEGIC_W1}/{STRATEGIC_W2} (Need / System Gap)")
print("Reason: preserves need as primary, while surfacing hidden vulnerability.")


df["Rank_StatusQuo"] = df["PC1"].rank(ascending=False, method="dense")

df["Rank_Strategic"] = df[strategic_col].rank(ascending=False, method="dense")

df["Priority_Jump"] = df["Rank_StatusQuo"] - df["Rank_Strategic"]

top_need_counties = df.sort_values("Rank_StatusQuo").head(10).copy()

movers = df.sort_values(
    ["Priority_Jump", "Rank_Strategic"],
    ascending=[False, True]
).head(10).copy()

fallers = df.sort_values(
    ["Priority_Jump", "Rank_Strategic"],
    ascending=[True, True]
).head(10).copy()

print("\n=== TOP 10 STATUS QUO COUNTIES (PC1 ONLY) ===")
print(
    top_need_counties[
        [
            "County, State",
            "Rank_StatusQuo",
            "Overall Food Insecurity Rate",
            "Child Food Insecurity Rate",
            "% FI > SNAP Threshold"
        ]
    ].round(6)
)

print("\n=== TOP MOVERS: HIDDEN VULNERABILITY COUNTIES ===")
print("These counties rise in priority when we account for the System Gap (PC2).")
print(
    movers[
        [
            "County, State",
            "Rank_StatusQuo",
            "Rank_Strategic",
            "Priority_Jump",
            "Child Food Insecurity Rate",
            "% FI > SNAP Threshold",
            "Cost Per Meal"
        ]
    ].round(6)
)

print("\n=== COUNTIES THAT FALL MOST ===")
print("These counties are strong on overall need but less driven by the System Gap.")
print(
    fallers[
        [
            "County, State",
            "Rank_StatusQuo",
            "Rank_Strategic",
            "Priority_Jump",
            "Overall Food Insecurity Rate",
            "Child Food Insecurity Rate",
            "% FI > SNAP Threshold"
        ]
    ].round(6)
)


rank_shift_summary = []

for w1 in [90, 80, 70, 60]:
    w2 = 100 - w1
    col_name = f"Ratio_{w1}_{w2}"

    rank_col = f"Rank_{w1}_{w2}"
    df[rank_col] = df[col_name].rank(ascending=False, method="dense")

    shift = (df["Rank_StatusQuo"] - df[rank_col]).abs()

    rank_shift_summary.append({
        "Scenario": f"{w1}/{w2}",
        "Total_Rank_Shift": int(shift.sum()),
        "Max_Individual_Shift": int(shift.max())
    })

rank_shift_df = pd.DataFrame(rank_shift_summary)

print("\n=== RANK SHIFT SUMMARY VS STATUS QUO (PC1 ONLY) ===")
print(rank_shift_df)


df.to_csv("county_results_full.csv", index=False)
scenario_summary.to_csv("scenario_summary_fixed.csv", index=False)
ratio_summary.to_csv("ratio_sensitivity_results.csv", index=False)
top_need_counties.to_csv("top_need_counties_pc1_only.csv", index=False)
movers.to_csv("top_movers_hidden_vulnerability_70_30.csv", index=False)
fallers.to_csv("counties_falling_under_70_30.csv", index=False)
rank_shift_df.to_csv("rank_shift_summary.csv", index=False)

print("\nFiles saved:")
print("- county_results_full.csv")
print("- scenario_summary_fixed.csv")
print("- ratio_sensitivity_results.csv")
print("- top_need_counties_pc1_only.csv")
print("- top_movers_hidden_vulnerability.csv")
print("- counties_falling.csv")
print("- rank_shift_summary.csv")


print("\n=== INTERPRETATION GUIDE ===")
print("PC1 = overall need factor")
print("PC2 = system gap / vulnerability factor")
print("Status quo ranking = PC1 only")
print(f"Strategic ranking = Blend of PC1 and PC2")
print("Priority_Jump > 0 means the county becomes more important when access gaps are considered.")
print("Use the MOVERS table for your slide, not just the top poverty counties.")