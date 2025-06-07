from train_model import main
import time
import logging

while True:
    logging.info("🕒 Sleeping for 10 minutes before next training...")
    time.sleep(600)
    main()