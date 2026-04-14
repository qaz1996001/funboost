
import  nb_log

from apscheduler.schedulers.background import BackgroundScheduler
import time

def my_job():
    print("Job executed!")

# Create scheduler
scheduler = BackgroundScheduler()



# Add task
scheduler.add_job(my_job, 'interval', seconds=1)
# Start scheduler
scheduler.start(paused=True)

while 1:
    try:
        print("Scheduler is running. Pausing for 10 seconds...")
        time.sleep(10)  # Run for 10 seconds

        # Resume scheduler
        scheduler.resume()
        print("Scheduler resumed.")

        time.sleep(10)  # Pause for 10 seconds

        # Pause scheduler
        scheduler.pause()
        print("Scheduler paused.")



    except (KeyboardInterrupt, SystemExit):
        # Stop scheduler
        scheduler.shutdown()
        print("Scheduler shutdown.")


