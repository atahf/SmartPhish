from openai import OpenAI
from bs4 import BeautifulSoup, Comment, Tag
import ast
import os
import requests
from lxml import html
import glob
import webbrowser
from PIL import ImageFile, Image, ImageOps
import magic
from icrawler.builtin import GoogleImageCrawler
from pathlib import Path
import colorsys
import easyocr
import re
import random
import time
import json

from template_manipulator import template_layout_randomizer

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
client = OpenAI(api_key=OPENAI_API_KEY)

def delete_all_files_in_folder(folder_path):
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return

    # Get a list of all files in the folder
    files = os.listdir(folder_path)

    # Iterate over each file and delete it
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Deleted file: {file_path}")
        except Exception as e:
            print(f"Error deleting file '{file_path}': {e}")

def get_image_path(folder_path):
    # Ensure the folder path exists
    if not os.path.exists(folder_path):
        print(f"The folder '{folder_path}' does not exist.")
        return None

    # Use glob to get a list of all files with a certain extension (e.g., '.jpg', '.png')
    image_files = glob.glob(os.path.join(folder_path, '*.jpg')) + glob.glob(os.path.join(folder_path, '*.png'))

    # Check if there is exactly one image file in the folder
    if len(image_files) == 1:
        return image_files[0]
    elif len(image_files) == 0:
        print(f"No image files found in the folder '{folder_path}'.")
    else:
        print(f"Multiple image files found in the folder '{folder_path}'. Expected only one.")

    return None

def download_image(url, save_path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        print(f"Image downloaded successfully and saved at {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")

def get_letter_borders(image_path,idx):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path)

    if result:
        bbox = result[0][0]

    # get the bounding box of the second character
        char_bbox = [
            [bbox[0][0] + idx * (bbox[1][0] - bbox[0][0]) / len(result[0][1]), bbox[0][1]],
            [bbox[0][0] + (idx+1) * (bbox[1][0] - bbox[0][0]) / len(result[0][1]), bbox[1][1]]
        ]
    
    # return the left and right borders of the second character
        return char_bbox[0][0], char_bbox[1][0]
    return 2,2

def create_new_logo(topic,idx):
    reader = easyocr.Reader(["en"],gpu=True)

    for filename in os.listdir("logo"):
        filepath= os.path.join("logo/",filename)
        image = Image.open(filepath)
        width, height = image.size
        start_x = 0
        end_x = width
        start_y = 0
        end_y = height
        result = reader.readtext(filepath,detail=1)
        text = ''.join([entry[1] for entry in result])
        print("OCRTEXT",text,"\n")
        #and text[0][1] and len(text[0][1])
        if text:
            bbox = text[0][0]
            left, right = get_letter_borders(filepath,idx)
            img_left = image.crop((0,0,left,height))
            img_right = image.crop((right,0,width,height))
            img_left.save("logo_m/"+filename+"modified.png")
            img_right.save("logo_m/"+filename+"modified2.png")
            
            left_image = Image.open("logo_m/"+filename+"modified.png")
            right_image = Image.open("logo_m/"+filename+"modified2.png")

    
            left_width, left_height = left_image.size
            right_width, right_height = right_image.size

      
            merged_width = left_width + right_width
            merged_height = max(left_height, right_height)

            if left_image.mode in ('RGBA', 'LA') or (left_image.mode == 'P' and 'transparency' in left_image.info):
                # Create a new image with transparency
                merged_image = Image.new('RGBA', (merged_width, merged_height))
            else:
                merged_image = Image.new('RGB', (merged_width, merged_height))

    
            merged_image.paste(left_image, (0, 0))
            merged_image.paste(right_image, (left_width, 0))

   
            merged_image.save("logo_m/"+filename+"modified3.png")
   
            os.remove("logo_m/"+filename+"modified.png")
            os.remove("logo_m/"+filename+"modified2.png")
            return "No Dall-E"
        
        else:
            # response = client.images.generate(
            #     model="dall-e-2",
            #     prompt="create a logo without background for a company promoting " + topic,
            #     size="256x256",
            #     quality="standard",
            #     n=1,
            #     )
            # image_url = response.data[0].url
            # return image_url
            return filepath
        return None
                        
def isHidden(T):
    style = T.get('style')

    if style is not None:
        obj = " ".join(str(style).replace(" ", "").split(";"))
        if "display:none" in obj or "visibility:hidden" in obj or "opacity:0" in obj:
            return True
    return False

def is_valid_image_url(url):
    types = ["jpeg", "jpg", "png", "svg", "ico"]

    try:
        ext = url[url.rfind(".") + 1:]
        if ext in types:
            return True
        else:
            response = requests.get(url, stream=True)
            response.raw.decode_content = True
            mime_type = magic.from_buffer(response.content, mime=True)
            return mime_type.startswith('image/')
    except Exception as e:
        print(e)
        return False

def getSize(URL):
    # the amount of bytes you will download
    resume_header = {'Range': 'bytes=0-2000000'}
    data = requests.get(URL, stream=True, headers=resume_header).content

    p = ImageFile.Parser()
    p.feed(data)  # feed the data to image parser to get photo info from data headers
    if p.image:
        return p.image.size
    return -1

def findAncestor(tag, anc_name):
    parent_tag = tag.parent

    while parent_tag != None and parent_tag.name != anc_name:
        parent_tag = parent_tag.parent

    return parent_tag

def int_convertable(string):
    try:
        int(string)
        return True
    except ValueError:
        return False

def isTrashImageForBody(tag):
    if tag.has_attr("height") and not tag.has_attr("width"):
        if int_convertable(tag["height"]) and int(tag["height"]) < 140:
            return True
    elif not tag.has_attr("height") and tag.has_attr("width"):
        if int_convertable(tag["width"]) and int(tag["width"]) < 220:
            return True
    elif not tag.has_attr("height") and not tag.has_attr("width"):
        return False
    else:
        if (int_convertable(tag["height"]) and int(tag["height"]) < 9) or (int_convertable(tag["width"]) and int(tag["width"]) < 9):
            return True
        elif  int_convertable(tag["height"]) and int_convertable(tag["width"]) and (int(tag["width"]) * int(tag["height"]) < 7000):
            return True

def isTrashImage(tag):
    if tag.has_attr("height") and not tag.has_attr("width"):
        if int_convertable(tag["height"]) and int(tag["height"]) < 40:
            return True
    elif not tag.has_attr("height") and tag.has_attr("width"):
        if int_convertable(tag["width"]) and int(tag["width"]) < 40:
            return True
    elif not tag.has_attr("height") and not tag.has_attr("width"):
        return False
    else:
        if (int_convertable(tag["height"]) and int(tag["height"]) < 9) or (int_convertable(tag["width"]) and int(tag["width"]) < 9):
            return True

def isSocialMediaImage(tag):
    if isTrashImage(tag):
        return False

    socialMedia = ["facebook", "tiktok", "twitter",
                   "instagram", "youtube", "twitch", "linkedin"]

    src_check = False
    alt_check = False
    size_check = False

    for x in socialMedia:
        if tag.has_attr("src") and x in tag["src"].lower():
            src_check = True

    if (tag.has_attr("alt") and tag["alt"].lower() in socialMedia):
        alt_check = True

    if tag.has_attr("height") and tag.has_attr("width") and int_convertable(tag["height"]) and int_convertable(tag["width"]):
        if (int(tag["height"]) == int(tag["width"]) or abs(int(tag["height"]) - int(tag["width"])) <= 10) and int(tag["height"]) < 45:
            size_check = True

    return src_check or alt_check or size_check

def isStoreImage(tag):
    if isTrashImage(tag):
        return False

    src_check = False
    alt_check = False
    size_check = False

    keywords = ["playstore", "googleplay",
                "googlestore", "appstore", "store", "applestore"]

    for x in keywords:

        if tag.has_attr("src") and x in tag["src"].lower():
            src_check = True
            break
        if (tag.has_attr("alt") and x in tag["alt"].lower().replace(" ", "")):
            alt_check = True
            break

    if tag.has_attr("width") and int_convertable(tag["width"]) and tag.has_attr("height") and int_convertable(tag["height"]):
        w = int(tag["width"])
        h = int(tag["height"])

        if w / h > 2.8 and w / h < 3.1 and w < 190 and h < 60:
            size_check = True

    return src_check or alt_check or size_check

def find_logo(tags, open_logo=False):
    for tag in tags:
        if tag.name == "img" and not isHidden(tag):
            found = False
            alt_pass = False
            ratio_pass = True
            url = ""
            url_pass = False
            cls_pass = False
            if tag.has_attr("src"):
                url = tag["src"]

            if tag.has_attr("alt"):
                if "logo" in tag["alt"].lower():
                    alt_pass = True

            if url.lower().find("logo") != -1:
                url_pass = True

            if tag.has_attr("class"):
                for c in tag["class"]:
                    if c.lower().find("logo") != -1:
                        cls_pass = True
                        break

            if alt_pass or url_pass or cls_pass:
                found = True
            else:
                h = 0
                w = 0
                if tag.has_attr("height") and tag.has_attr("width") and tag["height"].isdigit() and tag["width"].isdigit():
                    h = int(tag["height"])
                    w = int(tag["width"])
                else:
                    w, h = getSize(url)

                ratio = h / w
                # print(f"h({h}), w({w})")
                if h > 225 or w > 700:
                    ratio_pass = False
                    # print(f"huge")
                elif h < 23 or w < 23:
                    ratio_pass = False
                    # print(f"small")
                elif 0.0625 > ratio or ratio > 1.25:
                    # print(f"wierd")
                    ratio_pass = False

                if is_valid_image_url(url) and ratio_pass:
                    found = True

            if found:
                if open_logo:
                    webbrowser.open_new_tab(url)
                return tag

    return -1

def takeTableStyle(tag):
    table_ancestor = findAncestor(tag, "table")
    stringVersion = str(table_ancestor).split(
        ">")[0] + ">" + str(findAncestor(tag, "tr")) + "</table>"
    finalTag = BeautifulSoup(stringVersion, "html.parser").table
    return finalTag

def find_bodypic(tags, logo):
    tbr = []
    count = 0
    for tag in tags:
        if tag.name == "img" and not isSocialMediaImage(tag) and not isHidden(tag) and not isStoreImage(tag) and not isTrashImageForBody(tag):

            usefulTag = takeTableStyle(tag)
            if usefulTag not in tbr:
                if tag.has_attr("src") and logo == -1:
                    tag["id"] = "img_" + str(count)
                    count += 1
                    tbr.append(findAncestor(tag, "tr"))
                elif tag.has_attr("src") and tag["src"] != logo["src"]:
                    tag["id"] = "img_" + str(count)
                    count += 1
                    tbr.append(findAncestor(tag, "tr"))
    return tbr

def findMainImage(img_list):
    max_area = 4
    height = 2
    width = 2
    
    if (len(img_list) == 0):
        return None
    
    main_image = img_list[0]
    actual_tag = None
    for img in img_list:
        actual_tag = img
        img = str(img)
        if img.find("height=") != -1:
            height = img[img.find("height=")+8:img.find("\"",img.find("height=")+8)]
            if len(height)> 0 and height[-1] == "%":
                continue
            if len(height)> 0 and height[-1] == "x":
                height = height[:-2]
            if height.isnumeric() == False:
                height = 1
        if img.find("width=") != -1:
            width = img[img.find("width=")+7:img.find("\"",img.find("width=")+7)]
            if len(width)> 0 and width[-1] == "%":
                continue
            if len(width)> 0 and width[-1] == "x":
                width = width[:-2]
            if width.isnumeric() == False:
                width = 1
        area = int(height) * int(width)

        if area > max_area:
            
            max_area = area
            main_image = actual_tag
        
    return main_image

def get_full_text(tag):
    """
    Extracts all the text from a BeautifulSoup tag, including text in nested tags.

    Parameters:
    tag (bs4.element.Tag): A BeautifulSoup tag object.

    Returns:
    str: The full text contained within the tag.
    """
    return tag.get_text(separator=' ', strip=True)

def exists_in_list(l, q):
    index = 0
    for x in l:
        if q in x:
            return index
        index += 1
    
    return -1
            
def generator_by_text(prompt):
    #default_prompt = "I have extracted some text elements from an email, I will to give it to you as a python list. Then I want you to understand the context of this email, and change it to something completely different by changing specific list elements seperately. You dont have to change all elements. You must return the changed list. Distinguish the titles, paragraphs and action phrases (such as Buy Now) solely and change them. Do not change anything that does not contribute to the context of the email."
    response = client.chat.completions.create(
        model="gpt-4-1106-preview",
        messages=[
            {
                "role": "system",
                "content" : [{"type": "text", "text": "In your response, you must strictly follow the instructions given to you in the prompt!"}]
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    
                ],
            }
        ],
        temperature= 0.7,
        max_tokens=4000,  
    )
    print(response)
    return response.choices[0].message.content   

    
def find_texts_inside_tags(file_path,topic):
    #receiver_name = input("Choose a receiver name: ")
    #company_name = input("Choose a company name: ")
    
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
        all_tags = soup.find_all()
        for tag in all_tags:
            if isHidden(tag):
                tag.extract()
                
        a_tags = soup("a")
        for tag in a_tags:
            tag["href"] = "#"
        ##### EXPERIMENTAL #####
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            comment.extract()
        ##### EXPERIMENTAL #####
        td_tags = soup.find_all([ "h1", "h2", "p","td", "div","ul"])
        all_texts= []
        all_tags=[]
        for tag in td_tags:
            full_text = get_full_text(tag).strip()
            if full_text == "" :
                continue
            bigger_text = exists_in_list(all_texts, full_text)
            if bigger_text != -1:
                
                all_texts.pop(bigger_text)
                all_tags.pop(bigger_text)
            #and full_text.count('\xa0') < 2 and full_text.count('\xa0') < 2
            if full_text not in all_texts  and "display: none;" not in  str(tag) and "display:none;" not in  str(tag):
            
                all_texts.append(full_text)
                all_tags.append(tag)
                     
        prompt = """"""
        for x in all_tags:
            prompt += str(x) + "\n----------\n"
        prompt += f"""\n\nThese tags are extracted from the same email, I'm trying to identify the titles, regular paragraphs and the buttons in this email. Later, I want to change this identified components to create a completely different context. I want you to do this for me. Here are the specifications you must follow:
        1- Wipe out all of the existing content first, create the entire new content from scratch. Do not maintain any content from the previous version.
        2- Build a context around this topic: '{topic}'.
        3- You can only change the text parts of the tags.
        4- You cannot change any styles of the tags.
        5- You cannot modify the tag names, types, etc.
        6- Maintain the nested structure inside the tags.
        7- If you need a receiver name use generic salutations that can apply to any reader. Do not change the existing company name. You can improvise if you need any other names.
        8- Final content must be fully English.
        9- In your response, give the changed version of tags in the same format that is given to you (seperated by 10 dashes). Do not output anything else. In other words, output must be in this format: <tag>----------<tag>...<tag>
        10- Give all tags with respect to their occurance order in the prompt. All tags that were given to you as an input, must exist in the output in the same order.
        """
        print(prompt)
        response = generator_by_text(prompt)
        print(response)
        res_list = response.split("----------")
        for x in range(len(all_tags)):
            new_tag = BeautifulSoup(res_list[x], "html.parser")
            all_tags[x].replace_with(new_tag)
        

        return soup

def GetOriginalLogoandImage(html_data):
    logo = find_logo(html_data,False)
    logo_str = str(logo)
    logo_src = logo_str[logo_str.find("src=")+5:logo_str.find("\"",logo_str.find("src=")+5)]

    pics = find_bodypic(html_data,logo)
    if len(pics) > 0:
        image = findMainImage(pics)
        image_str = str(image)
        if image_str == "Fail":
            image_src = "Fail"
        else:
            image_src = image_str[image_str.find("src=")+5:image_str.find("\"",image_str.find("src=")+5)]
    else:
        image_src = "Fail"

    return logo_src, image_src

def getNewImage(image_query):
    google_Crawler_image = GoogleImageCrawler(storage = {'root_dir': r'image'})
    google_Crawler_image.crawl(keyword=image_query , max_num=1,overwrite=True)
    files = os.listdir('image')
    img_src = os.path.join('image/', files[0])
    img_format = files[0]
    img_format = img_format[img_format.rfind("."):]
    image = Image.open(img_src)
    w,h = image.size

    box = (0, 0, w, h*0.9)
    image = image.crop(box).save("image/x_cropped"+img_format)
    files = os.listdir('image')
    img_src = os.path.join('image/', files[-1])

    return img_src

def getDallImage(topic, company = None):
    prompt = f"Give me a basic illustration of '{topic}', do not involve any text. The picture should be easily understandable, and self explanatory. I will use this in an email that informs the user about the topic."
    if company != None:
        prompt = f"Give me a basic illustration of '{topic}' for {company}, do not involve any text. The picture should be easily understandable, and self explanatory. I will use this in an email that informs the user about the topic."
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        #quality="standard",
        n=1,
    )
    print(response.data[0].url)
    return response.data[0].url

def getNewLogo(original_logo_src,idx,topic):
    save_path = "logo/downloaded_logo.jpg"
    download_image(original_logo_src, save_path)
    new_logo_url = create_new_logo(topic,idx)

    if new_logo_url == "No Dall-E":
        folder_path = "logo_m"
        new_logo_url = get_image_path(folder_path)

    return new_logo_url

def move_file(source_file, destination_directory):
    time.sleep(10)
    file_name = os.path.basename(source_file)
    destination_path = os.path.join(destination_directory, file_name)
    os.rename(source_file, destination_path)

no_pic_topics = [
    "Suspicious Login Attempt",
    "Unusual Activity",
    "Password Reset Request",
    "Urgent Security Update Required",
    "Password Change Required",
    "Unauthorized Access",
    "Invalid Payment Details",
    "Invalid Shipment Adress",
    "Payment Failure",
    "Enable 2-Factor Authentication",
    "New Login Attempt",
    "Account Verification",
    "Credentials Leaked",
    "Security Breach Occured",
    "Policy Update",
    "Waiting for Payment"
]

topics = [
    "Phishing Alert and Safety Tips",
    "Bitcoin Rising",
    "Summer Sales",
    "New Year Sales",
    "Coupons Received",
    "You Received a Crypto Gift",
    "Update Your Account Information",
    "Discounts for Students",
    "Job Application",
    "Membership Advantages",
    "Black Friday Discounts",
    "Free Trial",
    "Free Coupons",
    "Incoming Events",
    "New Features",
    "Opportunites for Limited Time Only",
    "Enable 2-Factor Authentication",
]

def GeneratePhish(filename, output, topic=None):
    '''inputs: topic: email subject (ex. Job Application), filename: x.html
       output: modified email named phished.html will be written '''
    if topic == None:
        
        with open(filename, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            html_data = soup.find_all()
            logo = find_logo(html_data)
            body_pics = find_bodypic(html_data, logo)
            main_pic = findMainImage(body_pics)
        
        
        if main_pic == None:
            topic = random.choice(no_pic_topics)
        else:
            topic = random.choice(topics)
    
    
        
    soup = find_texts_inside_tags(filename,topic)
    if soup == None:
        raise Exception("Could Not Generate Content!")
    
    html_data = soup.find_all()
    logo = find_logo(html_data)
    body_pics = find_bodypic(html_data, logo)
    main_pic = findMainImage(body_pics)
    
    
    if main_pic != None:
        
        decide = random.choice([0,1])
        if decide:
            image_query = topic + " illustration"
            new_image_src = getNewImage(image_query)
            if new_image_src:
                move_file(new_image_src, filename[:filename.find('index.html')])
                new_image_src = new_image_src[new_image_src.rfind('/')+1:]
        else:
            tmp_url = getDallImage(topic)
            response = requests.get(tmp_url)
            if response.status_code == 200:
                if filename.rfind('/') != -1:
                    new_image_src = filename[:filename.rfind('/')+1]+"bodyImage.jpg"
                else:
                    new_image_src = filename[:filename.rfind('\\')+1]+"bodyImage.jpg"
                with open(new_image_src, 'wb') as f:
                    f.write(response.content)
                print("Image downloaded successfully.")
            else:
                new_image_src = None

        if new_image_src == None:
            raise Exception("Could Not Find/Generate the Image!")
        
        main_pic.img["src"] = new_image_src
    
    with open(output, 'w', encoding='utf-8') as file:
        file.write(str(soup))

def main(inputHTML, outputHTML):
    print("SmartPhish Generator started")
    try:
        #delete_all_files_in_folder("logo")
        #delete_all_files_in_folder("logo_m")
        delete_all_files_in_folder("image")

        
        GeneratePhish(inputHTML, outputHTML)
        print(f"Generated HTML is saved at {outputHTML}")
        output_path = "/".join(outputHTML.split("/")[:-1])
        #"/".join(s.split("/")[:-1])+"/randomized_1.html"
        template_layout_randomizer(outputHTML, output_path, density="hard")
    except Exception as e:
        print(f"Following error occured while generating!\n{e}")
