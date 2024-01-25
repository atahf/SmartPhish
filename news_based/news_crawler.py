from datetime import datetime
import feedparser
import requests
import json
from bs4 import BeautifulSoup, Tag

import concurrent.futures

def cnn(res):
    for category in ["world", "europe", "meast"]:
        cnn_feed = feedparser.parse(f"http://rss.cnn.com/rss/edition_{category}.rss")
        for entry in cnn_feed.entries:
            if "https://www.cnn.com/" in entry.link:
                try:
                    imgs = []
                    for elem in entry.links:
                        if "image" in elem.type:
                            imgs.append(elem.href)
                    article_response = requests.get(entry.link)
                    print(entry.link)
                    if article_response.status_code == 200:
                        soup = BeautifulSoup(article_response.text, 'html.parser')
                        posts = soup.find(id="posts-and-button")
                        if posts:
                            postLst = posts.find_all(['article'])
                            for post in postLst:
                                text_data = post.find(class_='post-content-rendered')
                                if text_data:
                                    text = ' '.join(list(text_data.stripped_strings)).strip() if len(text_data) > 1 else None
                                    if text != None:
                                        if len(post.find('header')) == 3:
                                            title = post.find('header').find('h2').string.strip()
                                            time = post.find('header').find('span').string.strip()
                                            if "Published" in time:
                                                time = time[time.find("Published")+9:].strip()
                                            elif "Updated" in time:
                                                time = time[time.find("Updated")+7:].strip()

                                            res["result"] += 1
                                            res["data"].append({
                                                "title": title,
                                                "date": time,
                                                "source": entry.link,
                                                "content": text,
                                                "images": imgs
                                            })

                        body =  soup.find('body')
                        if body.has_attr('data-page-type') and body['data-page-type'] == "article":
                            title = body.find(class_='headline__text').string.strip()
                            time = body.find(class_="timestamp").string.strip()
                            if "Published" in time:
                                time = time[time.find("Published")+9:].strip()
                            elif "Updated" in time:
                                time = time[time.find("Updated")+7:].strip()

                            text_content = [element for element in body.find(class_="article__content").find_all(class_=['paragraph', 'subheader']) if element.stripped_strings]
                            text = ' '.join(' '.join(element.stripped_strings) for element in text_content).strip()

                            res["result"] += 1
                            res["data"].append({
                                "title": title,
                                "date": time,
                                "source": entry.link,
                                "content": text,
                                "images": imgs
                            })
                except Exception as e:
                    print(e)

def bbc(res):
    bbc_feed = feedparser.parse("https://feeds.bbci.co.uk/news/world/rss.xml")
    for entry in bbc_feed.entries:
        try:
            imgs = []
            for elem in entry.links:
                if "image" in elem.type:
                    imgs.append(elem.href)
            single_page = requests.get(entry.id)
            print(entry.id)
            if single_page.status_code == 200:
                soup = BeautifulSoup(single_page.text, "html.parser")
                article = soup.find("article")

                title = article.find("h1").get_text()
                date = article.find("time", attrs={"data-testid": "timestamp"})["datetime"]
                texts = article.find_all("div", attrs={"data-component": "text-block"})
                text = ' '.join(t.get_text().strip() for t in texts if t.get_text() != None)
                
                if len(text) > 1:
                    res["result"] += 1
                    res["data"].append({
                        "title": title,
                        "date": date,
                        "source": entry.id,
                        "content": text,
                        "images": imgs
                    })
                    return res
        except Exception as e:
            print(e)

def al_jazeera(res):
    barbar_feed = feedparser.parse("https://www.aljazeera.com/xml/rss/all.xml")
    for entry in barbar_feed.entries:
        if "https://www.aljazeera.com/news/" in entry.link:
            try:
                imgs = []
                for elem in entry.links:
                    if "image" in elem.type:
                        imgs.append(elem.href)
                single_page = requests.get(entry.link)
                print(entry.link)
                if single_page.status_code == 200:
                    soup = BeautifulSoup(single_page.text, "html.parser")
                    article = soup.find("main")

                    title = article.find("h1").get_text()
                    date_container = article.find("div", class_="date-simple")
                    date = date_container.find("span").get_text()
                    container = article.find("div", class_="wysiwyg wysiwyg--all-content css-ibbk12")
                    texts = container.find_all(["p", "h2"])
                    text = ' '.join(t.get_text().strip() for t in texts if t.get_text() != None)
                    
                    if len(text) > 1:
                        res["result"] += 1
                        res["data"].append({
                            "title": title,
                            "date": date,
                            "source": entry.id,
                            "content": text,
                            "images": imgs
                        })
            except Exception as e:
                print(e)

def reuters(res):
    for category in ["europe", "middle-east"]:
        try:
            list_response = requests.get(f"https://www.reuters.com/world/{category}/")
            if list_response.status_code == 200:
                list_soup = BeautifulSoup(list_response.text, "html.parser")
                list_0 = list_soup.find_all("div", attrs={"data-testid": ["0", "Topic"]})
                for l in list_0:
                    posts = l.find_all("li")
                    for li in posts:
                        a_tag = li.find("a")
                        if a_tag:
                            if a_tag['href'] not in ["/world/europe/", "/world/middle-east/", "/world/"] and "/world/" in a_tag["href"]:
                                try:
                                    single_page = requests.get(f"https://www.reuters.com{a_tag['href']}")
                                    print(f"https://www.reuters.com{a_tag['href']}")
                                    if single_page.status_code == 200:
                                        soup = BeautifulSoup(single_page.text, "html.parser")
                                        article = soup.find("article")

                                        title = article.find("h1").get_text()
                                        date = article.find("time").get_text()
                                        texts = article.find_all(["p"])
                                        text = ' '.join(t.get_text().strip() for t in texts if t.get_text() != None and t["data-testid"].find("paragraph-") != -1)
                                        
                                        if len(text) > 1:
                                            res["result"] += 1
                                            res["data"].append({
                                                "title": title,
                                                "date": date,
                                                "source": f"https://www.reuters.com{a_tag['href']}",
                                                "content": text
                                            })
                                except Exception as e:
                                    print(e)
        except Exception as e:
            print(e)

def sozcu(res):
    for category in ["gundem", "dunya"]:
        try:
            list_response = requests.get(f"https://www.sozcu.com.tr/{category}")
            if list_response.status_code == 200:
                list_soup = BeautifulSoup(list_response.text, "html.parser")
                list = list_soup.find("div", class_="news-body")
                for d in list:
                    if isinstance(d, Tag):
                        a_tag = d.find("a")
                        try:
                            single_response = requests.get(a_tag["href"])
                            print(a_tag["href"])
                            if single_response.status_code == 200:
                                single_soup = BeautifulSoup(single_response.text, "html.parser")
                                article = single_soup.find("article")

                                title = article.find("h1").get_text()
                                date = article.find("div", class_="content-meta-dates").get_text()
                                text_container = article.find("div", class_="article-body")
                                texts = text_container.find_all(["p"])
                                text = ' '.join(t.get_text() for t in texts if t.get_text() != None)

                                if len(text) > 1:
                                    res["result"] += 1
                                    res["data"].append({
                                        "title": title,
                                        "date": date,
                                        "source": a_tag["href"],
                                        "content": text
                                    })
                        except Exception as e:
                            print(e)
        except Exception as e:
            print(e)

def cumhuriyet(res):
    for category in ["gundem", "dunya"]:
        try:
            list_response = requests.get(f"https://www.cumhuriyet.com.tr/{category}")
            if list_response.status_code == 200:
                list_soup = BeautifulSoup(list_response.text, "html.parser")
                list_container = list_soup.find("div", class_="content")
                list = list_container.find_all(["div"], class_="haber")
                for l in list:
                    a_tag = l.find("a")
                    if a_tag and a_tag['href'].find("video") == -1:
                        try:
                            single_response = requests.get(f"https://www.cumhuriyet.com.tr{a_tag['href']}")
                            print(f"https://www.cumhuriyet.com.tr{a_tag['href']}")
                            if single_response.status_code == 200:
                                single_soup = BeautifulSoup(single_response.text, "html.parser")
                                article_container = single_soup.find("div", class_="content")
                                article = article_container.find("div", class_="main-row")

                                title = article.find("h1").get_text()
                                dates = article.find_all("div", class_="yayin-tarihi")
                                date = ' '.join(t.get_text() for t in dates if t.get_text() != None).replace('\n', '').strip()

                                texts_container = article.find("div", class_="haberMetni")
                                texts = texts_container.find_all("p")
                                text = ' '.join(t.get_text() for t in texts if t.get("class") == None and t.get_text() != None)

                                if len(text) > 1:
                                    res["result"] += 1
                                    res["data"].append({
                                        "title": title,
                                        "date": date,
                                        "source": f"https://www.cumhuriyet.com.tr{a_tag['href']}",
                                        "content": text
                                    })
                        except Exception as e:
                            print(e)
        except Exception as e:
            print(e)

def hurriyet(res):
    for category in ["gundem", "dunya"]:
        try:
            list_response = requests.get(f"https://www.hurriyet.com.tr/{category}")
            if list_response.status_code == 200:
                list_soup = BeautifulSoup(list_response.text, "html.parser")
                list_container = list_soup.find("div", class_="category__list")
                list = list_container.find_all("div", class_="category__list__item")
                for l in list:
                    a_tag = l.find("a")
                    if a_tag:
                        try:
                            single_response = requests.get(f"https://www.hurriyet.com.tr{a_tag['href']}")
                            print(f"https://www.hurriyet.com.tr{a_tag['href']}")
                            if single_response.status_code == 200:
                                single_soup = BeautifulSoup(single_response.text, "html.parser")
                                article = single_soup.find("div", class_="Article")

                                title = article.find("h1").get_text()
                                date = article.find_all("p", class_="news-detail-text")[0].get_text()
                                text_container = article.find("div", class_="news-content readingTime")
                                texts = text_container.find_all("p")
                                text = ' '.join(t.get_text() for t in texts if t.get_text() != None)

                                if len(text) > 1:
                                    res["result"] += 1
                                    res["data"].append({
                                        "title": title,
                                        "date": date,
                                        "source": f"https://www.hurriyet.com.tr{a_tag['href']}",
                                        "content": text
                                    })
                        except Exception as e:
                            print(e)
        except Exception as e:
            print(e)

rss_urls = (
    "https://www.ukrinform.net/rss/block-lastnews",         # ['id', 'guidislink', 'title', 'title_detail', 'links', 'link', 'summary', 'summary_detail', 'published', 'published_parsed', 'tags']
    "https://euromaidanpress.com/feed/",                    # ['title', 'title_detail', 'links', 'link', 'authors', 'author', 'author_detail', 'published', 'published_parsed', 'tags', 'id', 'guidislink', 'summary', 'summary_detail', 'content']
    "https://www.independent.co.uk/topic/ukraine/rss",      # ['title', 'title_detail', 'links', 'link', 'summary', 'summary_detail', 'published', 'published_parsed', 'id', 'guidislink', 'media_content', 'media_credit', 'credit', 'media_text', 'authors', 'author', 'author_detail', 'updated', 'updated_parsed', 'tags']
    "https://en.interfax.com.ua/news/last.rss",             # ['title', 'title_detail', 'links', 'link', 'summary', 'summary_detail', 'published', 'published_parsed', 'id', 'guidislink', 'tags']
    "https://unn.ua/rss/news_uk.xml",                       # ['title', 'title_detail', 'summary', 'summary_detail', 'links', 'link', 'id', 'guidislink', 'tags', 'published', 'published_parsed']
    "https://zn.ua/rss/full.rss",                           # ['title', 'title_detail', 'links', 'link', 'published', 'published_parsed', 'tags', 'summary', 'summary_detail', 'content']
)

def crawl(rss_url, crawled_news):
    rss_feed = feedparser.parse(rss_url)
    for entry in rss_feed.entries:
        try:
            imgs = []
            for elem in entry.links:
                if "image" in elem.type:
                    imgs.append(elem.href)
            if rss_url == rss_urls[0] and entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    container = soup.find("div", class_="newsText")
                    divs = container.find_all("div", recursive=False)
                    article = divs[1]
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0 and t.get_text() != "Read also:")
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
            elif rss_url == rss_urls[1] and entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    article = soup.find("div", class_="entry-content")
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0 and t.get_text() != "Read also:")
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
            elif rss_url == rss_urls[2] and entry.link and "https://www.independent.co.uk/tv/" not in entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    article = soup.find("div", id="main")
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0)
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
            elif rss_url == rss_urls[3] and entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    article = soup.find("div", class_="article-content")
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0)
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
            elif rss_url == rss_urls[4] and entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    article = soup.find("div", class_="single-news-card_body__xHoem")
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0)
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
            elif rss_url == rss_urls[5] and entry.link:
                response = requests.get(entry.link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    body = soup.find("div", class_="content-wrap-inside")
                    article = body.find("article")
                    for child in article.find_all(recursive=False):
                        if child.name != 'p':
                            child.extract()
                    p_tags = article.find_all("p")
                    text = " ".join(t.get_text() for t in p_tags if len(t.get_text()) > 0)
                    crawled_news["result"] += 1
                    crawled_news["data"].append({
                        "title": entry.get("title", ""),
                        "source": entry.get("link", ""),
                        "content": text,
                        "date": entry.get("published", ""),
                        "images": imgs
                    })
        except Exception as e:
            continue

def crawl_news():
    crawled_news = {
        "result": 0,
        "date": datetime.now().isoformat(),
        "data": []
    }

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_results = [
            executor.submit(cnn, crawled_news),
            executor.submit(bbc, crawled_news),
            executor.submit(al_jazeera, crawled_news),
            executor.submit(reuters, crawled_news),
            executor.submit(sozcu, crawled_news),
            executor.submit(cumhuriyet, crawled_news),
            executor.submit(hurriyet, crawled_news)
        ]+[executor.submit(crawl, URL, crawled_news) for URL in rss_urls]

        concurrent.futures.wait(future_results)

        with open("news.json", 'w', encoding="utf-8") as f:
            json.dump(crawled_news, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":  
    crawl_news()
    
