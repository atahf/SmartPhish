import time
import os

from mail_utils import get_emails, send_email
from generator import main as generate

from dotenv import load_dotenv

load_dotenv()

EMAIL_ADDRESS = os.environ['EMAIL_ADDRESS']
PASSWORD = os.environ['EMAIL_APP_PASSWORD']

def pipeline():
    print("Starting pipeline...")
    while True:
        try:
            emails = get_emails(user=EMAIL_ADDRESS, password=PASSWORD, only_unread=True)
            
            for html, sender, company in emails:
                generate(inputHTML=html, outputHTML=html.replace("index", "output"))

                time.sleep(5)

        except Exception as e:
            print(e)
            print("\n=================\n*****************\nDue to Error will sleep for 10 seconds!\n*****************\n=================\n")
            time.sleep(10)

if __name__ == "__main__":
    pipeline()
