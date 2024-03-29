# SmartPhish

This repository is graduation project of
  - Ataollah Hosseinzadeh Fard [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ata-hosseinzadeh-433040191) 
  - Mete Harun Akçay [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/harunakcay/)
  - Emirhan Delican [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/emirhan-delican-ab801a228/)

This project aims to create a tool that takes an email as input and converts that email into phishing email using OpenAI's LLMs.
More details can be found inside [```report.pdf```](https://github.com/atahf/SmartPhish/blob/main/report.pdf)

## Usage
- After downloading the source code an additional ```.env``` file is needed.
- This ```.env``` file should have following structure with your own credentials.
  ```
  OPENAI_API_KEY={YOUR_OPENAI_API_KEY}
  EMAIL_ADDRESS={YOUR_EMAIL_ADDRESS}
  EMAIL_APP_PASSWORD={YOUR_EMAIL_APP_PASSWORD}
  ```
  - [this support](https://support.google.com/mail/answer/185833?hl=en) page can be used as guide to obtain "EMAIL_APP_PASSWORD" for your gmail.
- First things first, download all the needed dependencies from ```requirements.txt```
  ```
  pip install -r requirements.txt
  ```
- For generating phishing HTML from input run following
  ```
  python main.py generate [input_HTML_filepath] [output_HTML_filepath]
  ```
- The pipeline integrated with email is also avaiable. run with following
  ```
  python main.py pipeline
  ```
  - As soon as an email is received into inbox of email, it will be catched by pipeline; however, this process can be simulated by making any of emails inside inbox as unread or unseen.
- For the News-Based tool run following
  ```
  python main.py news-based (static|dynamic) [language]
  ```
  - example run
    ```
    python main.py news-based static english
    ```
