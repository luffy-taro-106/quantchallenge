import pandas as pd

# Load data
df = pd.read_csv("data.csv")

# Step 1: Create score_diff column
df["score_diff"] = df["home_score"] - df["away_score"]

# Step 2: Count consecutive "NOTHING" events before a non-NOTHING row
nothing_counts = []
count = 0

for event in df["event_type"]:
    if event == "NOTHING":
        count += 1
        nothing_counts.append(None)  # keep empty for "NOTHING" rows
    else:
        nothing_counts.append(count)
        count = 0  # reset

df["nothing_count_before_event"] = nothing_counts

# Step 3: Drop rows where event_type is "NOTHING"
df_filtered = df[df["event_type"] != "NOTHING"].reset_index(drop=True)

# Step 4: Drop the "enc" column (you said you don’t want it for modeling)
df_filtered = df_filtered.drop(columns=["enc"])

# Save modified dataset to new CSV
df_filtered.to_csv("data_modified.csv", index=False)

print("✅ Saved modified file as data_modified.csv")
