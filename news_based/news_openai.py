import os
import re
from openai import OpenAI
import json
import random
from datetime import datetime
from icrawler.builtin import GoogleImageCrawler
import easyocr
import cv2
from colorthief import ColorThief
import numpy as np
from PIL import Image
from io import BytesIO
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
    subject = out[out.find("Subject:")+8:out.find("Content:")].strip()
    text = out[out.find("Content:")+8:out.find("Button:")].strip()
    btn_text = out[out.find("Button:")+7:].strip()
    return subject, text, btn_text

def rgb_to_hex(rgb):
    r, g, b = rgb
    return "#{:02x}{:02x}{:02x}".format(b,g,r)

def hex_to_rgb(hex_color):
    return (int(hex_color[5:7], 16), int(hex_color[3:5], 16), int(hex_color[1:3], 16))

def get_bg_rgb(image_path):
    image = cv2.imread(image_path)
    height, width, _ = image.shape
    up = [(x, 0) for x in range(width)]
    bottom = [(x, height-1) for x in range(width)]
    left = [(0, y) for y in range(1,height-1)]
    right = [(width-1, y) for y in range(1,height-1)]
    positions = up + bottom + left + right

    rgbMap = {}
    occ = {}
    for pos in positions:
        x, y = pos
        if 0 <= x < width and 0 <= y < height:
            rgb = rgb_to_hex(image[y, x])
            rgbMap[rgb] = rgbMap.get(rgb, []) + [(x, y)]

    max_length = 0
    keys_with_max_length = []

    for key, values in rgbMap.items():
        length = len(values)
        if length > max_length:
            max_length = length
            keys_with_max_length = [key]
        elif length == max_length:
            keys_with_max_length.append(key)
    return random.choice(keys_with_max_length)

# Finds the Pixel with Highest Frequency
def get_bg_rgb2(filepath):
    img = cv2.imread(filepath)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    dim = (500, 300)
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
    unique, counts = np.unique(img.reshape(-1, 3), axis=0, return_counts=True)
    img[:,:,0], img[:,:,1], img[:,:,2] = unique[np.argmax(counts)]
    return img[0][0]

def amp_rgb(rgb):
    r, g, b = rgb
    if r > 200 and g > 200 and b > 200:
        print("old rgb: ", rgb, rgb_to_hex(rgb))
        rgb = [r-20, g-20, b-20]
        print("amplified rgb: ", rgb, rgb_to_hex(rgb))
    return rgb

def sRGB_to_linear(RGB):
    val = RGB / 255.0
    if val <= 0.04045:
        return val / 12.92
    else:
        return ((val + 0.055) / 1.055) ** 2.4
    
def calculate_luminance(color):
    R, G, B = color
    R_lin = sRGB_to_linear(R)
    G_lin = sRGB_to_linear(G)
    B_lin = sRGB_to_linear(B)
    luminance = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin
    return luminance

def contrast_ratio(color1, color2):
    luminance1 = calculate_luminance(color1)
    luminance2 = calculate_luminance(color2)
    if luminance1 > luminance2:
        return (luminance1 + 0.05) / (luminance2 + 0.05)
    else:
        return (luminance2 + 0.05) / (luminance1 + 0.05)

def adjust_text_color(bg_color, text_color, target_contrast=4.5):
    current_contrast = contrast_ratio(bg_color, text_color)

    if current_contrast >= target_contrast:
        return text_color

    adjustment_factor = target_contrast / current_contrast

    adjusted_text_color = (
        max(0, min(255, int((text_color[0] - bg_color[0]) * adjustment_factor + bg_color[0]))),
        max(0, min(255, int((text_color[1] - bg_color[1]) * adjustment_factor + bg_color[1]))),
        max(0, min(255, int((text_color[2] - bg_color[2]) * adjustment_factor + bg_color[2])))
    )

    return adjusted_text_color

def get_dominant_color(filepath):
    try:
        color_thief = ColorThief(filepath)
        dominant_color = rgb_to_hex(color_thief.get_color(quality=1))
    except Exception as e:
        if 'Empty pixels when quantize' in str(e):
            dominant_color = "#000000"
    return dominant_color

def checkCrawlURL(log_input):
    res = re.search(r"image #\d+\t(.*)", log_input.getMessage())
    if res:
        all_urls.append(log_input.args)

def get_logo(company, image_num=5):
    remove_dir("logoImages")
    all_urls.clear()
    good_urls = []
    google_Crawler_image = GoogleImageCrawler(storage = {'root_dir': r'logoImages'})
    google_Crawler_image.logger.disabled = True
    google_Crawler_image.feeder.logger.disabled = True
    google_Crawler_image.parser.logger.disabled = True
    google_Crawler_image.downloader.logger.addFilter(checkCrawlURL)
    google_Crawler_image.crawl(keyword=f"{company} logo", max_num=image_num)
    for tup in all_urls:
        ext = tup[1][tup[1].rfind('.'):].strip()
        fileName = f"logoImages/{'{:06d}'.format(tup[0])}{ext}"
        if ext == ".png":
            os.remove(fileName)
        else:
            img = cv2.imread(fileName)
            height, width, _ = img.shape
            if 0.75 > height/width or height/width > 1.25:
                os.remove(fileName)
            else:
                dominantC = get_dominant_color(fileName)
                bgC = get_bg_rgb(fileName)
                good_urls.append([tup[1], dominantC, bgC])
    remove_dir("logoImages")
    all_urls.clear()
    if len(good_urls) == 0:
        return get_logo(company, image_num+1)
    return random.choice(good_urls)

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
    for tup in all_urls:
        ext = tup[1][tup[1].rfind('.'):].strip()
        fileName = f"bodyImages/{'{:06d}'.format(tup[0])}{ext}"
        if ext == ".png":
            os.remove(fileName)
        else:
            try:
                img = cv2.imread(fileName)
                height, width = img.shape[:2]
                if height > width * 1.5 or height < 600:
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
        return get_image(query, image_num+1)
    return random.choice(good_urls)

def find_logo(topic, paragraph):
    query_generation = model.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        temperature=0.9,
        messages=[
            {
                "role": "system", 
                "content": "You are an assistant working in a reputable crowd sourcing company who reads given texts and their subjects and try to identify which company have written those texts."
            },
            {
                "role": "user",
                "content": f"""
                    give a real world company name that may send this text to readers, this company be well known and be appropriate in terms of geography and the context of text.
                    for example, if the text is about a donation campaign for a war in certain location, try to first find a charity located in that region, if not avaiable then try to find a global company.
                    if the text is charity related then find a known and related charity, otherwise, try to find a news agency that may have written that text.
                    IMPORTANT: for matter like war, if matter is related to one of sides, try to find company that is in their side, for example if text is about helping palestanian people in hamas-israil war, you cannot give company as red cross since thry do not help palestanians who are muslims!
                    IMPORTANT: return the name of company inside square brackets!
                    Subject: {topic}
                    Content: {paragraph}
                """
            }
        ]
    )
    return query_generation.choices[0].message.content

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
                    You have to give at most 3 words as keyword from following topic and paragraph.
                    The keywords cannot be more than 3! For example, if the title and text is about a matter on war in somewhere, as keyword you should return war, location.
                    Topic: {topic}
                    Paragraph: {paragraph}
                """
            }
        ]
    )
    keys = query_generation.choices[0].message.content
    return f"recent {keys.replace(' ', '+').replace(',', '')} last-minute-news images"

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
                "content": """
                    You are an assistant working in a reputable news agency who paraphrases news to get the attention of the readers.
                """
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
                    Try to generate an imaginary and clickbait news while leveraging given news, but if you cannot generate such news then do one of following:
                        - If the news is related to war, earthquake etc. the output message should be a charity organization for affected poors to make readers donate.
                        - If it is related to health, the output may be some text inviting reader to take the related health test.
                        - If it is economic i.e a tax refund, you may invite the users to calculate their refunds.
                    My examples are not mandatory, you decide which scenerio would be better to create a message so as to make readers interested.
                    Your output should be realistic, formal no exaggerations.
                    IMPORTANT: Your output should be approximately 100 words.
                    IMPORTANT: Your output should be related to the input.
                    Your output structure has to be this: 
                    Subject: subject of your output news
                    Content: content of your output news
                    Button: text that is written in the button. (maximum 4 words)
                """
            }
        ]
    )
    subject, text, btn_text = parse_output(task.choices[0].message.content)
    print(f"-------- GENERATED TEXT --------\nsubject: {subject}\ntext: {text}\nbutton text: {btn_text}\n")
    
    company_query = find_logo(subject, text)
    while '[' not in company_query and ']' not in company_query:
        company_query = find_logo(subject, text)
    company = company_query[company_query.find('[')+1:company_query.find(']')]
    logo_url, logo_DC, bgLogo = get_logo(company)
    print(f"-------- LOGO URL --------\ncompany: {company}\nURL: {logo_url}\ndominant color: {logo_DC}\nbg-color: {bgLogo}")

    #logo_DC = rgb_to_hex(adjust_text_color(hex_to_rgb(bgLogo), hex_to_rgb(logo_DC), 7.5))
    #print(f"adjusted dominant color according to bg-color: {logo_DC}\n")

    img_query = find_image(subject, text)
    img_url = get_image(img_query)
    print(f"-------- IMAGE SEARCH QUERY --------\n{img_query}\nURL: {img_url}\n")

    ouputfile = rf"news_based\outputs\output_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.html"
    genNedit_template(
        infileName=f"news_based/templates/template4.html",
        texts=[text],
        logoURL=logo_url,
        bgColor=bgLogo,
        imageURLs=[img_url],
        titles=[{"text": subject, "color": logo_DC}],
        button={"text": btn_text, "bg-color": logo_DC},
        dividers=[logo_DC, logo_DC, logo_DC],
        companyName=company,
        companyAddress="  ",
        unsubText="Click here to Unsubscribe",
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
