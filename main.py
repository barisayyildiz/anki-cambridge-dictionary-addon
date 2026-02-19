import requests
from bs4 import BeautifulSoup
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Upgrade-Insecure-Requests": "1",
    "Cookie": "JSESSIONID=E582279278938B01D713CBC84F4CB905-n1"
}

def get_all_words():
    page = 1
    all_words = []
    while True:
        url = f"https://dictionary.cambridge.org/plus/wordlist/88939097/entries/{page}/"
        response = requests.get(url, headers=headers)
        data = response.json()
        if len(data) == 0:
            break
        all_words.extend(data)
        page += 1
        time.sleep(0.2)
    return all_words

def download_audio(url, out_path):
    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(r.content)

def main():
    words = get_all_words()
    for word in words:
        print(word.get("entryUrl"))
        entryHtml = requests.get(word.get("entryUrl"), headers=headers).text
        soup = BeautifulSoup(entryHtml, 'html.parser')
        sense_id = word.get("senseId")
        print(sense_id)
        
        sound_path = f"./sounds/Cambridge_{word.get("id")}.mp3"
        if word.get("soundUSMp3") != None:
            download_audio(word.get("soundUSMp3"), sound_path)

        sentencesHtml = soup.select(
            f'div.def-block[data-wl-senseid="{sense_id}"] div.def-body div.examp.dexamp'
        )
        # how to map the text from sentences
        sentences = [s.text for s in sentencesHtml]
        # print(sentences)

if __name__ == "__main__":
    main()
