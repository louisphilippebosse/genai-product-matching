import pandas as pd

def process_uploaded_file(file):
    """
    Process and clean the uploaded file.
    - Validates that the file has only one column.
    - Removes duplicates and empty rows.
    - Normalizes text data.

    Args:
        file: The uploaded file (e.g., from Flask's request.files).

    Returns:
        A cleaned pandas DataFrame.
    """
    try:
        # Load the uploaded file into a DataFrame
        df = pd.read_csv(file)

        # Validate that the file has only one column
        if df.shape[1] != 1:
            raise ValueError("Uploaded file must contain exactly one column.")

        # Rename the column for consistency
        df.columns = ["text"]

        # Drop rows with empty or null values
        df = df.dropna()

        # Strip whitespace from text entries
        df["text"] = df["text"].str.strip()

        # Convert text to lowercase for normalization
        df["text"] = df["text"].str.lower()

        # Drop duplicate rows after normalization
        df = df.drop_duplicates()

        return df

    except Exception as e:
        raise ValueError(f"Error processing file: {e}")