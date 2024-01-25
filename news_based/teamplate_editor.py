from bs4 import BeautifulSoup, Tag
import random

def rgb_to_hex(rgb):
    r, g, b = rgb
    return "#{:02x}{:02x}{:02x}".format(b,g,r)

def hex_to_rgb(hex_color):
    return (int(hex_color[5:7], 16), int(hex_color[3:5], 16), int(hex_color[1:3], 16))

def getStyleRule(style_tag, rule, new_entry):
    styleStr = style_tag.string
    ruleS = styleStr.find(rule)
    ruleE = styleStr[ruleS:].find('}')+ruleS+1
    attrStr = styleStr[ruleS:ruleE]
    attrS = attrStr.find(new_entry[0])
    attrE = attrStr[attrS:].find(';')+attrS+1
    newAttr = f"{new_entry[0]}: {new_entry[1]};"
    newRule = attrStr[:attrS]+newAttr+attrStr[attrE:]
    newStyle = styleStr[:ruleS]+newRule+styleStr[ruleE:]
    return newStyle

def genNedit_template(infileName, logoURL=None, imageURLs=[], texts=[], titles=[], button=None, dividers=[], unsubText=None, companyName=None, companyAddress=None, bgColor=None, outfileName="output.html"):
    with open(infileName, "r", encoding="utf-8") as file:
        html = file.read()
    soup = BeautifulSoup(html, "html.parser")
    
    if bgColor:
        style_tag = soup.find("style")
        style_tag.string = getStyleRule(style_tag, ".main", ["background-color", bgColor])
        style_tag.string = getStyleRule(style_tag, ".wrapper", ["background-color", bgColor+'f0'])
        if len([x for x in hex_to_rgb(bgColor) if x < 200]) > 1:
            style_tag.string = getStyleRule(style_tag, ".wrapper", ["color", '#ffffff'])

    if logoURL:
        logo = soup.find(id="logo")
        if logo and logo.has_attr("src"):
            logo["src"] = logoURL
    
    for i in range(len(imageURLs)):
        tmpImg = soup.find(id=f"img-{i}")
        if tmpImg and tmpImg.has_attr("src"):
            tmpImg["src"] = imageURLs[i]
            tmpImg["width"] = "100%"

    for i in range(len(texts)):
        tmpText = soup.find(id=f"text-{i}")
        if tmpText:
            tmpText.string = texts[i]

    for i in range(len(titles)):
        tmpTitle = soup.find(id=f"title-{i}")
        if tmpTitle and tmpTitle.has_attr("style"):
            tmpTitle.string = titles[i]["text"]
            if titles[i]['color'] != None:
                tmpTitle["style"] = f"color: {titles[i]['color']}"

    if button:
        style_tag = soup.find("style")
        if style_tag:
            if button["bg-color"] != None:
                style_tag.string = getStyleRule(style_tag, ".button", ["background-color", button["bg-color"]])
            tmpBtn = soup.find(class_="button")
            if tmpBtn:
                tmpBtn.string = button["text"]

    for i in range(len(dividers)):
        tmpDivider = soup.find(id=f"divider-{i}")
        if tmpDivider and tmpDivider.has_attr("style"):
            tmpDivider["style"] = f"background-color: {dividers[i]}"

    if unsubText:
        unsubTextTag = soup.find(id="text-unsub")
        if unsubTextTag:
            unsubTextTag.string = unsubText

    if companyName:
        companyNameTag = soup.find(id="company-name")
        if companyNameTag:
            companyNameTag.string = companyName

    if companyAddress:
        companyAddressTag = soup.find(id="company-address")
        if companyAddressTag:
            companyAddressTag.string = companyAddress

    with open(outfileName, "w", encoding="utf-8") as output_file:
        output_file.write(str(soup))
