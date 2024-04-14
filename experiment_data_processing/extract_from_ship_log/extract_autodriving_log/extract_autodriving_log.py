import os
import pandas as pd
import ast


def process_log_data(file_path, keys):
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    folder_name = f"{base_name}_data"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    extracted_data = []

    with open(file_path, 'r') as file:
        previous_time = None
        for line_number, line in enumerate(file):
            if line.strip():
                try:
                    _, json_str = line.split(" : ")
                    data = ast.literal_eval(json_str)  # Convert string to dictionary
                    if data.get('flag_autodrive') == True:  # Check if flag_autodrive is True
                        if 'time' in data:
                            # Format the time to ensure consistency to two decimal places
                            current_time = float(data['time'])
                            # Check if previous_time has been set
                            if previous_time is not None:
                                # Calculate time difference
                                time_difference = current_time - previous_time
                            else:
                                # Set time difference to 0 for the first record
                                time_difference = 0

                            # Extract only required keys
                            record = {key: data.get(key, None) for key in keys}
                            record['time_difference'] = round(time_difference,
                                                              2)  # Use time difference rounded to two decimal places
                            extracted_data.append(record)

                            # Update previous_time to current_time
                            previous_time = current_time
                except ValueError:
                    print("Error parsing JSON or processing data on line:", line)

    # Convert data to DataFrame and save as CSV
    df = pd.DataFrame(extracted_data)
    csv_file_path = os.path.join(folder_name, f"{base_name}.csv")
    df.to_csv(csv_file_path, index=False)

    # Save the same data to TXT
    txt_file_path = os.path.join(folder_name, f"{base_name}.txt")
    with open(txt_file_path, 'w') as file:
        for item in extracted_data:
            file.write(str(item) + "\n")


# Example usage
file_path = 'autonomous_driving_extracted_log_one_cycle.txt'
keys = ["latitude", "longitude", "heading", "velocity", "pwml_chk", "pwmr_chk"]  # List of keys to extract

process_log_data(file_path, keys)