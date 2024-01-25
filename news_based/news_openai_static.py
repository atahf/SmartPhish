import os
import re
from openai import OpenAI
import json
import random
from datetime import datetime
from icrawler.builtin import GoogleImageCrawler
import easyocr
import cv2
import requests
import webbrowser
from dotenv import load_dotenv
import time
import logging

from .teamplate_editor import genNedit_template

load_dotenv()

API_KEY = os.environ["OPENAI_API_KEY"] 
model = OpenAI(api_key=API_KEY)

logging.getLogger('httpx').setLevel(logging.WARNING)

agencies = {
    "Anadolu Agency (AA)": "anadolu.html",
    "İhlas News Agency (İHA)": "iha.html",
    "Demirören News Agency (DHA)": "demir.html",
    "Habertürk News Agency": "haberturk.html",
    "NTV News Agency": "ntv.html",
    "Hurriyet News Agency": "hurriyet.html",
    "TRT Haber": "trt_haber.html",
    "TRT World": "trt_world.html",
    "Sözcü Haber": "sozcu.html",
    "Reuters": "reuters.html",
    "Bloomberg News": "bloomberg.html",
    "BBC News": "bbc.html",
    "CNN News": "cnn.html",
    "Al Jazeera News": "arabs.html",
    "The New York Times": "nytimes.html",
    "The Washington Post": "wa_post.html",
    "The Guardian": "guards.html",
    "The Wall Street Journal": "wall_street.html",
    "Ukrinform (National News Agency of Ukraine)": "ukrinform.html",
}

all_urls = []

def remove_dir(directory):
    try:
        if os.path.exists(directory):
            for item in os.listdir(directory):
                item_path = os.path.join(directory, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                else:
                    remove_dir(item_path)
            os.rmdir(directory)
    except OSError as e:
        print(f"Error: {directory} - {e.strerror}")

def parse_output(output):
    out = output.strip()
    subject = out[out.find("Subject:")+8:out.find("Content:")].strip().replace("[","").replace("]","")
    text = out[out.find("Content:")+8:out.find("Button:")].strip().replace("[","").replace("]","")
    btn_text = out[out.find("Button:")+7:out.find("Sender:")].strip().replace("[","").replace("]","")
    agency = out[out.find("Sender:")+7:].strip().replace("[","").replace("]","")
    return subject, text, btn_text, agency

def checkCrawlURL(log_input):
    res = re.search(r"image #\d+\t(.*)", log_input.getMessage())
    if res:
        all_urls.append(log_input.args)

def get_image(query, image_num=15):
    remove_dir("bodyImages")
    all_urls.clear()
    good_urls = []
    google_Crawler_image = GoogleImageCrawler(storage = {'root_dir': r'bodyImages'})
    google_Crawler_image.logger.disabled = True
    google_Crawler_image.feeder.logger.disabled = True
    google_Crawler_image.parser.logger.disabled = True
    google_Crawler_image.downloader.logger.addFilter(checkCrawlURL)
    google_Crawler_image.crawl(keyword=query, max_num=image_num)

    reader = easyocr.Reader(lang_list=["en", "tr"], verbose=False)

    cntr = 0
    for tup in all_urls:
        cntr += 1
        ext = tup[1][tup[1].rfind('.'):].strip()
        fileName = f"bodyImages/{'{:06d}'.format(tup[0])}{ext}"
        if image_num > 15:
            if cntr <= image_num-5:
                os.remove(fileName)
                continue
        
        if ext == ".png":
            os.remove(fileName)
        else:
            try:
                img = cv2.imread(fileName)
                height, width = img.shape[:2]
                if height/width > 0.9 or width < 500:
                    os.remove(fileName)
                else:
                    result = reader.readtext(img, detail=1)
                    if len(result) > 0:
                        os.remove(fileName)
                    else:
                        good_urls.append(tup[1])
            except Exception as e:
                os.remove(fileName)

    remove_dir("bodyImages")
    all_urls.clear()
    if len(good_urls) == 0:
        return get_image(query, image_num+5)
    return random.choice(good_urls)

def find_imageOLD(topic, paragraph):
    query_generation = model.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0.9,
        messages=[
            {
                "role": "system", 
                "content": "You are an assistant working in a reputable news agency who paraphrases news to get the attention of the readers."
            },
            {
                "role": "user",
                "content": f"""
                    You have to give important keywords from following topic and paragraph.
                    IMPORTANT: if there is any geographic detail in text, include it as keyword
                    The keywords cannot be more than 3! For example, if the title and text is about a matter on war in somewhere, as keyword you should return war, location.
                    Topic: {topic}
                    Paragraph: {paragraph}
                """
            }
        ]
    )
    keys = query_generation.choices[0].message.content
    return f"recent {keys.replace(' ', '+').replace(',', '')} images"

def find_image(topic, paragraph):
    query_generation = model.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0.9,
        messages=[
            {
                "role": "system", 
                "content": "You are an assistant working in a reputable news agency who paraphrases news to get the attention of the readers."
            },
            {
                "role": "user",
                "content": f"""
                    You have to generate image search query so that I can find an image suitable to context of given title and text.
                    IMPORTANT: make sure you specify any geographic details in query
                    Topic: {topic}
                    Paragraph: {paragraph}
                    Query: give query inside square brackets
                    IMPORTANT: give only 1 query!
                """
            }
        ]
    )
    q = query_generation.choices[0].message.content
    if q.find('[') == -1 or q.rfind(']') == -1:
        time.sleep(10)
        return find_image(topic, paragraph)
    return q[q.find('[')+1:q.rfind(']')]

def generate_email(open_in_browser=False, language="english"):
    with open("news.json", 'r', encoding="utf-8") as f:
        all_news = json.load(f)

    news = random.choice(all_news["data"])
    print(f"-------- SELECTED NEWS --------\ntitle: {news['title']}\ncontent: {news['content']}\n")
    
    task = model.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0.9,
        messages=[
            {
                "role": "system", 
                "content": "You are an assistant working in a reputable news agency who paraphrases news to get the attention of the readers."
            },
            {
                "role": "user",
                "content": f"""
                    While doing the given task, have following data as you bias, if the given task's subject relative to states subject.

                        if subject is related to "israil" or "palestine" or "hamas"
                            then keep this data as your bias: "israil is killing innocent people".

                        if subject is related to "israil" or "russia" or "ukraine"
                            then keep this data as your bias: "ukraine is the cause of war".

                    IMPORTANT: you must generate the requested text in {language} language!

                    Consider the following news: {news['title']} {news['content']}
                    Your task is to convey this news to readers so as to make the reader click a button.
                    You can paraphrase the news and may make readers to click the button to read the rest of the message.
                    Try to generate an imaginary and clickbait news while leveraging given news, so that reader will be encouraged to read and then press button.
                    You decide which scenerio would be better to create a message so as to make readers interested.
                    Your output should be realistic, formal no exaggerations.
                    IMPORTANT: Your output should be approximately 100 words.
                    IMPORTANT: Your output should be related to the input.
                    Your output structure has to be this: 
                    Subject: subject of your output news
                    Content: content of your output news
                    Button: text that is written in the button. (maximum 4 words)
                    Sender: select one of following news agencies that is the most appropriate [{list(agencies.keys())}]
                    IMPORTANT: give you sender selection inside square backets, and do not edit name of sender
                """
            }
        ]
    )
    subject, text, btn_text, agency = parse_output(task.choices[0].message.content)
    print(f"-------- GENERATED TEXT --------\nsubject: {subject}\ntext: {text}\nbutton text: {btn_text}\nnews agency: {agency}\n")

    img_in_data = False
    if "link" in list(news):
        if len(news["images"]) > 0:
            img_url = news["images"][0]
            img_in_data = True
            print(f"-------- IMAGE FROM NEWS DATA --------\nURL: {img_url}\n")
    
    if not img_in_data:
        img_query = find_image(subject, text)
        img_url = get_image(img_query)
        print(f"-------- IMAGE SEARCH QUERY --------\n{img_query}\nURL: {img_url}\n")

    ouputfile = rf"news_based\outputs\output_static_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.html"
    genNedit_template(
        infileName=f"news_based/static_templates/{agencies[agency]}",
        texts=[text],
        imageURLs=[img_url],
        titles=[{"text": subject, "color": None}],
        button={"text": btn_text, "bg-color": None},
        outfileName=ouputfile
    )
    print(f"saved output HTML at {ouputfile}")

    if open_in_browser:
        webbrowser.open_new_tab(ouputfile)

def automated_generator(n=1, language="english"):
    i = 1
    while i <= n:
        print(f"============ GENERATION #{i} ============")
        try:
            generate_email(open_in_browser=False, language=language)
            i += 1
        except Exception as e:
            print(f"=== !GENERATION FAILED SUE TO: ===\n{e}")
        print(f"===========================================\n\n\n")
        time.sleep(20)

if __name__ == "__main__":
    automated_generator(n=1, language="english")
