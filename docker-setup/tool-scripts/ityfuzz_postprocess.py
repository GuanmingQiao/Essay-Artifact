import os
import json
import sys

def process_coverage_files(coverage_folder, target_file):
    coverage_files = sorted([f for f in os.listdir(coverage_folder) if f.startswith("cov_") and f.endswith(".json")])
    
    if not coverage_files:
        print("No coverage files found in the specified folder.")
        return

    first_timestamp = int(coverage_files[0].split('_')[1].split('.')[0])

    with open(target_file, 'w') as output_file:
        for filename in coverage_files:
            timestamp_str = filename.split('_')[1].split('.')[0]
            timestamp = int(timestamp_str)
            time_lapsed = (timestamp - first_timestamp) // 1000000
            file_path = os.path.join(coverage_folder, filename)
            with open(file_path, 'r') as coverage_file:
                coverage_data = json.load(coverage_file)
                for key, value in coverage_data.items():
                    branch_covered = value["branch_coverage"]
                    instructions_covered = value["instruction_coverage"]
                    output_file.write(f"{time_lapsed}m: {branch_covered} Edges, {instructions_covered} Instrs\n")

def filter_last_row_per_time(input_file, output_file):
    with open(input_file, 'r') as file:
        lines = file.readlines()

    last_row_per_time = {}
    
    for line in lines:
        time_lapsed = line.split(':')[0]
        last_row_per_time[time_lapsed] = line.split(':')[1].strip()

    # Find the maximum time_lapsed
    max_time_lapsed = max(int(time.split('m')[0]) for time in last_row_per_time.keys())
    last_value = last_row_per_time["0m"]

    # Fill in missing minutes
    filled_rows = []
    for minute in range(max_time_lapsed + 1):
        time_key = f"{minute}m"
        if time_key in last_row_per_time:
            filled_rows.append(time_key + ": " + last_row_per_time[time_key])
            last_value = last_row_per_time[time_key]
        else:
            # Use the last available row for the missing minute
            filled_rows.append(time_key + ": " + last_value)
    
    with open(output_file, 'w') as file:
        for row in filled_rows:
            file.write(row + '\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py <coverage_folder_path> <target_file_path>")
        sys.exit(1)

    coverage_folder_path = sys.argv[1]
    target_file_path = sys.argv[2]
    process_coverage_files(coverage_folder_path, target_file_path)
    filter_last_row_per_time(target_file_path, target_file_path)