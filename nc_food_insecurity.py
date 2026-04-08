import pandas as pd
import matplotlib.pyplot as plt

# Load workbook and use ONLY the County sheet
file_path = "C:/Users/fishk/Downloads/MMG2025_2019-2023_Data_To_Share.xlsx"
df = pd.read_excel(file_path, sheet_name="County")

# Filter to North Carolina counties
nc = df[df["State"] == "NC"].copy()

# Aggregate to yearly statewide rates
# Weighted statewide rate = total food insecure persons / implied total population
yearly = (
    nc.groupby("Year")
      .apply(lambda g: pd.Series({
          "Overall Food Insecurity Rate (%)": (
              g["# of Food Insecure Persons Overall"].sum() /
              (g["# of Food Insecure Persons Overall"] / g["Overall Food Insecurity Rate"]).sum()
          ) * 100,
          "Child Food Insecurity Rate (%)": (
              g["# of Food Insecure Children"].sum() /
              (g["# of Food Insecure Children"] / g["Child Food Insecurity Rate"]).sum()
          ) * 100,
          "County Average Overall Rate (%)": g["Overall Food Insecurity Rate"].mean() * 100,
          "Total Food Insecure Persons": g["# of Food Insecure Persons Overall"].sum(),
          "Total Food Insecure Children": g["# of Food Insecure Children"].sum()
      }))
      .reset_index()
)

# Year-over-year change
yearly["YoY Change Overall (pp)"] = yearly["Overall Food Insecurity Rate (%)"].diff()
yearly["YoY Change Child (pp)"] = yearly["Child Food Insecurity Rate (%)"].diff()

print("\nNorth Carolina yearly food insecurity summary:\n")
print(yearly.round(2))

# Time series plot
plt.figure(figsize=(10, 6))
plt.plot(yearly["Year"], yearly["Overall Food Insecurity Rate (%)"], marker="o",
         label="Overall Food Insecurity Rate")
plt.plot(yearly["Year"], yearly["Child Food Insecurity Rate (%)"], marker="o",
         label="Child Food Insecurity Rate")
plt.xlabel("Year")
plt.ylabel("Rate (%)")
plt.title("North Carolina Food Insecurity Trends (County Sheet, 2019–2023)")
plt.xticks(yearly["Year"])
plt.legend()
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("nc_food_insecurity_time_series.png", dpi=300)
plt.show()

# Optional export for reporting
yearly.round(2).to_csv("nc_food_insecurity_yearly_summary.csv", index=False)
