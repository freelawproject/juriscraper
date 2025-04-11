# Juriscraper Scheduler

This scheduler automatically runs all the juriscraper classes from the specified folders at 6:00 AM every day and also every 10 minutes.

## Folders Scanned

The scheduler scans the following folders for juriscraper classes:
- `juriscraper/opinions/united_states/federal_district`
- `juriscraper/opinions/united_states/federal_appellate`
- `juriscraper/opinions/united_states/federal_bankruptcy`
- `juriscraper/opinions/united_states/state`

## Requirements

- Python 3.6+
- Required packages are listed in `requirements.txt`

## Installation

1. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the scheduler:
```
python scheduler.py
```

The scheduler will:
1. Wait for the next scheduled time (6:00 AM or the next 10-minute interval)
2. Run at 6:00 AM every day
3. Run every 10 minutes

## Logging

Logs are written to both the console and a file named `juriscraper_scheduler.log`.

## How It Works

The scheduler:
1. Discovers all Python files in the specified folders
2. Imports each module and finds the `Site` class
3. Creates an instance of the `Site` class and runs it
4. Processes all opinions from the site
5. Updates the crawl configuration details

## Troubleshooting

If you encounter any issues:
1. Check the log file for error messages
2. Ensure all required packages are installed
3. Verify that the folder paths are correct 