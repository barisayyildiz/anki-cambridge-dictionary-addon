from aqt.qt import *
from aqt import mw, gui_hooks
from aqt.utils import showInfo
from anki import hooks
from bs4 import BeautifulSoup
import requests
import os

profile = "User 1"
sound_path = os.path.join(
    os.path.expanduser("~"),
    ".local", "share", "Anki2", profile, "collection.media"
)

class CambridgeSyncDialog(QDialog):
    SOURCE_FIELDS = [
        "id", "headword", "definition", "pos",
        "soundUS", "soundUK",
        "example_1", "example_2", "example_3", "example_4", "example_5",
        "entryUrl"
    ]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cambridge Wordlist Sync")
        self.config = mw.addonManager.getConfig(__name__) or {}
        self.mapping_combos = {}

        # Layout
        main_layout = QVBoxLayout()
        
        # Settings Group
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout()

        self.jsessionid_input = QLineEdit()
        self.jsessionid_input.setText(self.config.get("jsessionid", "06ED2C0B8BEFC1A02073640DE2A28BED-n1"))
        settings_layout.addRow("JSESSIONID:", self.jsessionid_input)

        self.wordlist_input = QLineEdit()
        self.wordlist_input.setText(self.config.get("wordlist_id", "88939097"))
        settings_layout.addRow("Wordlist ID:", self.wordlist_input)

        self.deck_selector = QComboBox()
        self.deck_selector.addItems(mw.col.decks.all_names())
        if self.config.get("target_deck"):
            self.deck_selector.setCurrentText(self.config.get("target_deck"))
        settings_layout.addRow("Target Deck:", self.deck_selector)

        self.model_selector = QComboBox()
        self.model_selector.addItems(sorted([m['name'] for m in mw.col.models.all()]))
        if self.config.get("target_model"):
            self.model_selector.setCurrentText(self.config.get("target_model"))
        self.model_selector.currentIndexChanged.connect(self.on_model_change)
        settings_layout.addRow("Note Type:", self.model_selector)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Mappings Group
        mapping_group = QGroupBox("Field Mapping")
        mapping_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.mapping_grid = QGridLayout()
        scroll_content.setLayout(self.mapping_grid)
        scroll.setWidget(scroll_content)
        
        mapping_layout.addWidget(scroll)
        mapping_group.setLayout(mapping_layout)
        main_layout.addWidget(mapping_group)

        # Sync button
        self.sync_button = QPushButton("Sync")
        self.sync_button.clicked.connect(self.on_sync)
        main_layout.addWidget(self.sync_button)

        self.setLayout(main_layout)
        self.resize(600, 700)
        
        # Trigger initial mapping load
        self.on_model_change()

    def on_model_change(self):
        # Clear existing items
        for i in reversed(range(self.mapping_grid.count())): 
            self.mapping_grid.itemAt(i).widget().setParent(None)
        self.mapping_combos = {}

        model_name = self.model_selector.currentText()
        model = mw.col.models.by_name(model_name)
        if not model: return
        
        field_names = [f['name'] for f in model['flds']]
        saved_mappings = self.config.get("model_mappings", {}).get(model_name, {})

        # Add Headers
        self.mapping_grid.addWidget(QLabel("<b>Cambridge Data</b>"), 0, 0)
        self.mapping_grid.addWidget(QLabel("<b>Anki Field</b>"), 0, 1)

        for i, source in enumerate(self.SOURCE_FIELDS):
            self.mapping_grid.addWidget(QLabel(source), i+1, 0)
            
            combo = QComboBox()
            combo.addItem("<Ignore>", None)
            combo.addItems(field_names)
            
            # Default or Saved selection
            if source in saved_mappings and saved_mappings[source] in field_names:
                combo.setCurrentText(saved_mappings[source])
            else:
                # heuristic matching
                for f in field_names:
                    # simpler heuristic: match if source key is contained in field key
                    # e.g. "headword" in "Front (Headword)"
                    # We might want to Map "headword" -> "Front" though.
                    # Let's keep it simple for now.
                    if f.lower() in source.lower() or source.lower() in f.lower():
                        combo.setCurrentText(f)
                        break
            
            self.mapping_grid.addWidget(combo, i+1, 1)
            self.mapping_combos[source] = combo

    def save_settings(self):
        jsessionid = self.jsessionid_input.text().strip()
        wordlist_id = self.wordlist_input.text().strip()
        model_name = self.model_selector.currentText().strip()
        
        current_mapping = {
            src: combo.currentText() 
            for src, combo in self.mapping_combos.items() 
            if combo.currentText() != "<Ignore>"
        }
        
        all_mappings = self.config.get("model_mappings", {})
        all_mappings[model_name] = current_mapping

        self.config.update({
            "jsessionid": jsessionid,
            "wordlist_id": wordlist_id,
            "target_deck": self.deck_selector.currentText(),
            "target_model": model_name,
            "model_mappings": all_mappings
        })
        mw.addonManager.writeConfig(__name__, self.config)

    def closeEvent(self, event):
        self.save_settings()
        event.accept()

    def on_sync(self):
        self.save_settings()
        
        jsessionid = self.config["jsessionid"]
        wordlist_id = self.config["wordlist_id"]
        deck_name = self.deck_selector.currentText().strip()
        model_name = self.model_selector.currentText().strip()
        current_mapping = self.config["model_mappings"].get(model_name, {})
        deck_id = mw.col.decks.id(deck_name)
        
        if not wordlist_id:
            showInfo("Please enter a Wordlist ID.")
            return

        # Run Sync
        sync_wordlist(wordlist_id, deck_id, jsessionid, model_name, current_mapping)
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

def sync_wordlist(wordlist_id, deck_id, jsessionid, model_name, mapping):
    config = mw.addonManager.getConfig(__name__) or {}
    ignored_ids = set(config.get("ignored_ids", []))

    entries = fetch_all_entries(wordlist_id, jsessionid)
    added = 0
    model = mw.col.models.by_name(model_name)
    mw.col.models.set_current(model)

    for e in entries:
        source_id = str(e["id"])
        
        if source_id in ignored_ids:
            continue
        
        # Check for duplicates using SourceID if mapped, otherwise just proceed (or use a dedicated ID field if possible)
        # For now, let's assume we want to avoid dupes. We can search in the first mapped field 
        # but that's risky. Ideally we have a dedicated ID field.
        # Let's search if "SourceID" is in the mapping or we just check if we have a note with this SourceID
        # The previous code hardcoded "SourceID". We should functionality to map an ID field, but for now
        # let's proceed without strict dup checking for custom types for now unless mapped.
        
        # Actually, let's just create the note.
        note = mw.col.newNote()
        
        # Data preparation
        data = {
            "id": source_id,
            "headword": e.get("headword", ""),
            "definition": e.get("definition", ""),
            "pos": e.get("pos", ""),
            "entryUrl": e.get("entryUrl", "")
        }

        # Check for duplicates if Source ID is mapped
        if "id" in mapping:
            target_field = mapping["id"]
            if target_field:
                safe_id = source_id.replace('"', '\\"')
                query = f'"{target_field}:{safe_id}"'
                if mw.col.find_notes(query):
                    continue


        # Sentences
        entry_url = e.get("entryUrl")
        if entry_url:
            try:
                entry_html = requests.get(entry_url, headers=get_headers(jsessionid)).text
                soup = BeautifulSoup(entry_html, 'html.parser')
                sense_id = e.get("senseId")
                if sense_id:
                    sentencesHtml = soup.select(
                        f'div.def-block[data-wl-senseid="{sense_id}"] div.def-body div.examp.dexamp'
                    )
                    sentences = [s.text.strip() for s in sentencesHtml]
                    for idx in range(5):
                        key = f"example_{idx+1}"
                        if idx < len(sentences):
                            data[key] = sentences[idx]
                        else:
                            data[key] = ""
            except Exception as err:
                print(f"Error fetching sentences for {data['headword']}: {err}")

        # Downloads
        if "soundUS" in mapping.keys():
            us_url = e.get("soundUSMp3")
            if us_url:
                filename = f"Cambridge_US_{source_id}.mp3"
                try:
                    download_sound(us_url, filename, jsessionid)
                    data["soundUS"] = f"[sound:{filename}]"
                except:
                    pass
        
        if "soundUK" in mapping.keys():
            uk_url = e.get("soundUKMp3")
            if uk_url:
                filename = f"Cambridge_UK_{source_id}.mp3"
                try:
                    download_sound(uk_url, filename, jsessionid)
                    data["soundUK"] = f"[sound:{filename}]"
                except:
                    pass

        # Apply mapping
        has_mapped_fields = False
        for source_field, target_field in mapping.items():
            if target_field and source_field in data:
                note[target_field] = data[source_field]
                has_mapped_fields = True
        
        # Minimal duplicate check if "SourceID" field exists in note type? 
        # Previous code used 'SourceID' field. Let's keep it if the user maps it? 
        # For now, just add.
        
        if has_mapped_fields:
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

def on_notes_deleted(col, note_ids):
    config = mw.addonManager.getConfig(__name__) or {}
    ignored_ids = set(config.get("ignored_ids", []))
    added_new = False
    
    for nid in note_ids:
        try:
            note = mw.col.getNote(nid)
            # Find the ID field name for this note's model
            target_field = config.get("model_mappings", {}).get(note.model()['name'], {}).get("id")
            if target_field and target_field in note:
                deleted_cambridge_id = note[target_field]
                if deleted_cambridge_id:
                    ignored_ids.add(deleted_cambridge_id)
                    added_new = True
        except Exception as e:
            print(f"Error processing deleted note: {e}")
            
    if added_new:
        config["ignored_ids"] = list(ignored_ids)
        mw.addonManager.writeConfig(__name__, config)

hooks.notes_will_be_deleted.append(on_notes_deleted)
