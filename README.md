# SmartPhish

This repository is graduation project of
  - Ataollah Hosseinzadeh Fard [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ata-hosseinzadeh-433040191) 
  - Mete Harun Akçay [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/harunakcay/)
  - Emirhan Delican [![](https://img.shields.io/badge/LinkedIn-0077B5?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/emirhan-delican-ab801a228/)


## Usage
- After downloading the source code an additional ```.env``` file is needed.
- This ```.env``` file should have following structure with your own credentials.
  ```
  OPENAI_API_KEY={YOUR_OPENAI_API_KEY}
  EMAIL_ADDRESS={YOUR_EMAIL_ADDRESS}
  EMAIL_APP_PASSWORD={YOUR_EMAIL_APP_PASSWORD}
  ```
- First things first, download all the needed dependencies from ```requirements.txt```
  ```
  pip install -r requirements.txt
  ```
- For the News-Based tool run following
  ```
  python main.py news-based (static|dynamic) [language]
  ```
  - example run
    ```
    python main.py news-based static english
    ```
