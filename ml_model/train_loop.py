# train_loop.py

# This script runs train_model.py periodically invoking the main training function
# every 10 minutes to retrain the model with updated patient data.

from train_model import main
import time
import logging

# Infinite loop to run the training process every 10 minutes
while True:
    logging.info("🕒 Sleeping for 10 minutes before next training...")
    time.sleep(600)
    main()