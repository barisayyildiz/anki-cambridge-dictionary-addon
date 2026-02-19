from aqt.qt import *
from aqt import mw
from aqt.utils import showInfo
from bs4 import BeautifulSoup
import requests
import os

profile = "User 1"
sound_path = os.path.join(
    os.path.expanduser("~"),
    ".local", "share", "Anki2", profile, "collection.media"
)

class CambridgeSyncDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cambridge Wordlist Sync")

        # Layout
        layout = QVBoxLayout()

        # JSESSIONID input
        layout.addWidget(QLabel("Cambridge JSESSIONID Token"))
        self.jsessionid_input = QLineEdit()
        self.jsessionid_input.setText("06ED2C0B8BEFC1A02073640DE2A28BED-n1")
        layout.addWidget(self.jsessionid_input)

        # Wordlist ID input
        layout.addWidget(QLabel("Cambridge Wordlist ID:"))
        self.wordlist_input = QLineEdit()
        self.wordlist_input.setText("88939097")
        layout.addWidget(self.wordlist_input)

        # Deck selector
        layout.addWidget(QLabel("Select Anki Deck:"))
        self.deck_selector = QComboBox()
        self.deck_selector.addItems(mw.col.decks.all_names())
        layout.addWidget(self.deck_selector)

        # Sync button
        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.on_sync)
        layout.addWidget(self.sync_button)

        self.setLayout(layout)

    def on_sync(self):
        jsessionid = self.jsessionid_input.text().strip()
        wordlist_id = self.wordlist_input.text().strip()
        deck_name = self.deck_selector.currentText().strip()
        deck_id = mw.col.decks.id(deck_name)
        if not wordlist_id:
            showInfo("Please enter a Wordlist ID.")
            return
        print(wordlist_id, deck_id, jsessionid)
        sync_wordlist(wordlist_id, deck_id, jsessionid)
        self.close()

def get_headers(cookie):
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Upgrade-Insecure-Requests": "1",
        "Cookie": f"JSESSIONID={cookie}"
    }

# [sound:word_A20703.mp3]

def download_sound(url, file_name, cookie):
    r = requests.get(url, headers=get_headers(cookie), timeout=10)
    r.raise_for_status()
    with open(os.path.join(sound_path, file_name), "wb") as f:
        f.write(r.content)

def sync_wordlist(wordlist_id, deck_id, jsessionid):
    entries = fetch_all_entries(wordlist_id, jsessionid)
    added = 0
    for e in entries:
        source_id = str(e["id"])
        if mw.col.find_notes(f'SourceID:"{source_id}"'):
            continue
        model = mw.col.models.by_name("Basic")
        mw.col.models.set_current(model)        
        note = mw.col.newNote()
        # print(note.fields)
        note["Word"] = e["headword"]
        note["Definition"] = e["definition"]
        note["SourceID"] = source_id

        entry_url = e["entryUrl"]
        entry_html = requests.get(entry_url, headers=get_headers(jsessionid)).text
        soup = BeautifulSoup(entry_html, 'html.parser')
        sense_id = e["senseId"]
        sentencesHtml = soup.select(
            f'div.def-block[data-wl-senseid="{sense_id}"] div.def-body div.examp.dexamp'
        )
        sentences = [s.text for s in sentencesHtml]

        for idx in range(min(5, len(sentences))):
            note[f"Sentence{idx+1}"] = sentences[idx]

        # save sound
        sound_file_name = f"Cambridge_{source_id}.mp3"
        if e["soundUSMp3"] != None:
            download_sound(e["soundUSMp3"], sound_file_name, jsessionid)
            note["Sound"] = f"[sound:{sound_file_name}]"
        
        mw.col.addNote(note)
        mw.col.decks.select(deck_id)
        added += 1

    mw.col.save()
    showInfo(f"Added {added} new words to '{mw.col.decks.name(deck_id)}'.")


def fetch_all_entries(wordlist_id, cookie):
    page = 1
    entries = []

    while True:
        url = f"https://dictionary.cambridge.org/plus/wordlist/{wordlist_id}/entries/{page}/"
        r = requests.get(
            url,
            headers=get_headers(cookie),
            timeout=10,
        )
        data = r.json()
        if not data:
            break
        entries.extend(data)
        page += 1
    print(f"Fetched {len(entries)} entries from Cambridge Wordlist.")
    return entries

action = QAction("Sync Cambridge Wordlist", mw)
action.triggered.connect(lambda: CambridgeSyncDialog().exec())
mw.form.menuTools.addAction(action)
