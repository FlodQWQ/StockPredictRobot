import requests
import re
from config import *
from bs4 import BeautifulSoup


def get_content(name, cnt):
    contents = []
    for i in range(0, cnt+1):
        pn = 10 * i
        url = f"http://www.baidu.com/s?rtt=1&bsst=1&cl=2&tn=news&ie=utf-8&word={name}&pn={pn}"
        content = get_url(url).text
        index = content.find("<h3 class=")
        content = content[index:]
        pattern = r'<a href="http.*?aria-label="标题：.*?</a>'
        matches = re.findall(pattern, content, re.DOTALL)
        for match in matches:
            soup = BeautifulSoup(match, 'html.parser')
            a_tag = soup.find('a')
            if a_tag is not None:
                attributes = dict(a_tag.attrs)
                contents.append((attributes['href'], attributes['aria-label']))
    # print(contents[:cnt*10])
    return contents[:cnt*10]


def get_url(url):
    i = 0
    while i < MAX_RETRY:
        try:
            html = requests.get(url, timeout=5)
            return html
        except requests.exceptions.RequestException:
            i += 1

