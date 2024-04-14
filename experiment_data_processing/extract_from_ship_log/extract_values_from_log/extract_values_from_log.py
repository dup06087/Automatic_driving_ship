import os
import pandas as pd
import ast


def process_log_data(file_path, keys):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    folder_name = f"{base_name}_data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    extracted_data = {}

    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():
                _, json_str = line.split(" : ")
                try:
                    data = ast.literal_eval(json_str)  # Convert string to dictionary
                    if 'time' in data:
                        # Format the time to ensure consistency to two decimal places
                        formatted_time = "{:.2f}".format(float(data['time']))
                        # Extract only required keys and update the time to formatted time
                        record = {key: data.get(key, None) for key in keys}
                        record['time'] = formatted_time  # Update time in the record
                        # Use formatted time as the key to ensure latest entry is saved
                        extracted_data[formatted_time] = record
                except ValueError:
                    print("Error parsing JSON or processing data on line:", line)

    # Convert the dictionary to a list of dictionaries for DataFrame conversion
    final_data = list(extracted_data.values())

    # Convert data to DataFrame and save as CSV
    df = pd.DataFrame(final_data)
    csv_file_path = os.path.join(folder_name, f"{base_name}.csv")
    df.to_csv(csv_file_path, index=False)

    # Save the same data to TXT
    txt_file_path = os.path.join(folder_name, f"{base_name}.txt")
    with open(txt_file_path, 'w') as file:
        for item in final_data:
            file.write(str(item) + "\n")


# Example usage
file_path = 'autodrive_extracted_log_one_cycle.txt'
keys = ["latitude", "longitude", "dest_latitude", "dest_longitude", "time"]  # List of keys to extract

process_log_data(file_path, keys)
