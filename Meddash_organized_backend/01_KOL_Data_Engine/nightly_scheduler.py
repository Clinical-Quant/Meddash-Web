import schedule
import time
import subprocess
import logging
import sys

# Configure logging for the schedule service
logging.basicConfig(
    filename="scheduler_service.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def job():
    logging.info("Running scheduled pipeline job...")
    print("Executing run_pipeline.py...")
    try:
        # Run the pipeline script orchestrator
        result = subprocess.run([sys.executable, "run_pipeline.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info("Pipeline job finished successfully.")
            print("Pipeline run completed successfully.")
        else:
            logging.error(f"Pipeline job failed. Error: {result.stderr}")
            print("Pipeline run encountered an error. Check scheduler_service.log and meddash_pipeline.log.")
    except Exception as e:
        logging.error(f"Failed to execute pipeline: {e}")

# Schedule the job to run every day at 02:00 AM
schedule.every().day.at("02:00").do(job)

if __name__ == "__main__":
    logging.info("Scheduler started. Waiting for 02:00 AM to run the pipeline.")
    print("Scheduler is running. It will execute the Meddash pipeline daily at 02:00 AM.")
    print("Leave this terminal open. Press Ctrl+C to exit.")

    while True:
        try:
            schedule.run_pending()
            time.sleep(60) # Sleep for a minute between checks
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")
            logging.info("Scheduler stopped manually.")
            break
