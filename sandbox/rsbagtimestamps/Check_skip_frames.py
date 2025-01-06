import csv
import argparse

def check_consecutive_zeros(file_path):
    all_ok = True
    print(f"{file_path}:")
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        next(reader)  # Skip the row after the header

        previous_row = None
        previous_row_number = 1  # Start after skipping the first two rows
        current_row_number = 2   # Start tracking rows from the third row (1-indexed)

        for row in reader:
            current_row_number += 1
            # Extract timestamp and `d_dur`, `rgb_dur` as integers
            try:
                timestamp = row[1]  # Assuming 'timestamp' is the second column
                d_dur = int(row[-2])
                rgb_dur = int(row[-1])
            except ValueError:
                print(f"{file_path}: Skipping invalid row:", row)
                all_ok = False
                continue

            if previous_row is not None:
                prev_timestamp, prev_d_dur, prev_rgb_dur = previous_row

                # Check for consecutive zeros in the same positions
                if (prev_d_dur == 0 and d_dur == 0) or (prev_rgb_dur == 0 and rgb_dur == 0):
                    print(f"{file_path}: Consecutive Zeros at row {previous_row_number} (timestamp: {prev_timestamp}) "
                          f"and row {current_row_number} (timestamp: {timestamp})")
                    all_ok = False

            previous_row = (timestamp, d_dur, rgb_dur)
            previous_row_number = current_row_number
    if all_ok:
        print(f"{file_path}: No problems detected")
    else:
        print(f"{file_path}: Problems detected")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for consecutive zeros in specific columns of a CSV file.")
    parser.add_argument("path", type=str, help="Path to the CSV file")
    args = parser.parse_args()
    
    check_consecutive_zeros(args.path)
