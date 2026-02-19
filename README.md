# Anki Cambridge Dictionary Import Addon

This Anki addon allows you to sync vocabulary from your personal Cambridge Dictionary wordlists directly into Anki. It fetches definitions, audio pronunciations (US & UK), part of speech, and example sentences, automatically creating rich cards for your language learning.

## Features

- **Sync Personal Wordlists:** Import words saved in your Cambridge Dictionary account.
- **Rich Data Import:**
  - **Headword**, **Definition**, **Part of Speech**
  - **Audio:** Automatically downloads and attaches US and UK pronunciation audio.
  - **Context:** Fetches up to 5 example sentences per word.
  - **Source URL:** Links back to the original dictionary entry.
- **Flexible Field Mapping:** Map Cambridge data fields to any field in your Anki note types.
- **Duplicate Prevention:** Skips words that have already been imported (requires mapping the `id` field).

## Installation

1.  Copy the `anki-cambridge-addon` folder into your Anki addons directory:
    - **Linux:** `~/.local/share/Anki2/addons21/`
    - **Windows:** `%APPDATA%\Anki2\addons21\`
    - **Mac:** `~/Library/Application Support/Anki2/addons21/`
2.  Restart Anki.

## Configuration & Usage

### 1. Get your Cambridge Credentials

To sync your private wordlists, the addon needs access to your session.

1.  Log in to [Cambridge Dictionary](https://dictionary.cambridge.org/).
2.  Open your browser's Developer Tools (F12) and go to the **Application** (Chrome/Edge) or **Storage** (Firefox) tab.
3.  Under **Cookies**, find `https://dictionary.cambridge.org`.
4.  Copy the value of the `JSESSIONID` cookie.
5.  Navigate to your Wordlist page on the website.
6.  Copy the **Wordlist ID** from the URL (e.g., `https://dictionary.cambridge.org/plus/wordlist/88939097/...` -> `88939097`).

### 2. Syncing in Anki

1.  Open Anki.
2.  Go to **Tools** > **Sync Cambridge Wordlist**.
3.  **Settings:**
    - Paste your **JSESSIONID** and **Wordlist ID**.
    - Select the **Target Deck** where you want new cards to appear.
    - Select the **Note Type** you want to use (e.g., "Basic", "Cloze", or a custom type).
4.  **Field Mapping:**
    - The addon will try to automatically match Cambridge data fields to your Note Type fields.
    - Manually adjust mapping as needed (e.g., Map `headword` to "Front", `definition` to "Back").
    - **Important:** Map the `id` field to a dedicated field in your note type (e.g., "SourceID") to enable duplicate checking.
5.  Click **Sync**.

The addon will download the wordlist, fetch details including audio and sentences, and add the new notes to your deck.

## Requirements

- Anki 2.1+
