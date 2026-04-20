import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

df = pd.read_csv('FoodInsecuritybyState.xlsx - State.csv')
data_2023 = df[df['Year'] == 2023].copy()

features = ['Overall Food Insecurity Rate', 'Cost Per Meal', 'Weighted Annual Food Budget Shortfall']
X = data_2023[features]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
data_2023['Cluster'] = kmeans.fit_predict(X_scaled)
data_2023['Cluster'] = data_2023['Cluster'].astype(str)


plt.figure(figsize=(12, 7))
sns.scatterplot(
    data=data_2023,
    x='Overall Food Insecurity Rate',
    y='Weighted Annual Food Budget Shortfall',
    hue='Cluster',
    size='Cost Per Meal',
    sizes=(50, 400),
    palette='Set2',
    alpha=0.7
)


nc_row = data_2023[data_2023['State Name'] == 'North Carolina']
plt.scatter(
    nc_row['Overall Food Insecurity Rate'],
    nc_row['Weighted Annual Food Budget Shortfall'],
    color='red',
    s=500,
    marker='*',
    label='North Carolina',
    edgecolors='black'
)


plt.title('State-Level Food Insecurity Clusters (2023)')
plt.xlabel('Overall Food Insecurity Rate')
plt.ylabel('Annual Food Budget Shortfall ($)')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()


plt.savefig('nc_cluster_analysis.png')
plt.show()


nc_cluster_id = nc_row['Cluster'].values[0]
peers = data_2023[data_2023['Cluster'] == nc_cluster_id]['State Name'].tolist()
print(f"NC Cluster ID: {nc_cluster_id}")
print(f"Peer States: {peers}")