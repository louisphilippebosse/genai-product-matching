import pandas as pd

# Define file paths
files = {
    "Data_Internal": "../Data_Internal.csv",
    "Data_External": "../Data_External.csv"
}

# Process each file
for name, path in files.items():
    try:
        # Load the data
        print(f"Processing {name} from {path}...")
        df = pd.read_csv(path)

        # If the file is external, keep only the first column
        if name == "Data_External":
            df = df.iloc[:, [0]]  # Keep only the first column

        # Drop rows where all values are NaN (empty)
        df_cleaned = df.dropna(how='all')

        # Save the cleaned data
        output_path = f"{name}_cleaned.csv"
        df_cleaned.to_csv(output_path, index=False)
        print(f"Cleaned data saved to {output_path}")
    except FileNotFoundError:
        print(f"File not found: {path}")
    except Exception as e:
        print(f"An error occurred while processing {path}: {e}")