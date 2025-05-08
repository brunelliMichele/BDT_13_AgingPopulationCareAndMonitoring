import pandas as pd
import time
import argparse

# Function to simulate the data stream replicating the real time of the observations
def simulateDataStream(csv_path, limit = None):

    print(f"Loading data from {csv_path}...")
    # loading and sorting the data
    df = pd.read_csv(csv_path, parse_dates = ["DATE"])
    df = df.sort_values(by = "DATE").reset_index(drop = True)

    # check if the user selects a limit
    if limit:
        df = df.iloc[:limit]

    first_TS = df.iloc[0]["DATE"]
    start_time = time.time()

    # simulate the data stream
    for _, row in df.iterrows():
        current_time = row["DATE"]
        time_since_start = (current_time - first_TS).total_seconds()
        elapsed = time.time() - start_time
        delay = max(0, time_since_start - elapsed)
        time.sleep(delay)
        obs = {
            "timestamp": row["DATE"],
            "patient": row["PATIENT"],
            "description": row["DESCRIPTION"],
            "value": row["VALUE"],
            "units": row["UNITS"]
        } 
        print(obs)

# test code
path_observations = "data/csv/medical/observations.csv"
simulateDataStream(path_observations)

""" # for running with cli
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required = True, help = "Insert the path to a csv file")
    parser.add_argument("--limit", type = int, help = "Number of row to simulate")
    args = parser.parse_args()

    simulateDataStream(args.csv, args.limit) """