# TikTok Email Checker and Info Grabber

This tool combines functionalities from two Python scripts to check TikTok user availability and associated email addresses (Gmail, Yahoo, Hotmail, AOL, Mail.ru), and then retrieves detailed TikTok user information, sending the results to a Telegram bot.

## Features

- **TikTok User Search**: Uses `livecounts.xyz` API to find TikTok usernames.
- **Email Availability Check**: Checks if a TikTok username is associated with available email addresses across multiple domains (Gmail, Yahoo, Hotmail, AOL, Mail.ru) using `AegosPy`.
- **TikTok User Information Retrieval**: Fetches detailed information about TikTok users (ID, Name, Bio, Region, Private status, Followers, Following, Likes, Video Count) using `AegosPy`.
- **Telegram Integration**: Sends detailed results to a specified Telegram chat ID using a bot token.
- **Multi-threaded**: Designed to run checks concurrently using multiple threads.
- **Dynamic User-Agent Generation**: Generates realistic user agents for TikTok API requests.

## Installation

To install and run this tool, you need Python 3 and the following libraries. It's recommended to use a virtual environment.

1.  **Clone the repository (if applicable) or download the script:**

    ```bash
    git clone https://github.com/Madr50/Tik.git
    cd Tik
    # Or if you downloaded the merged_tiktok_tool.py directly, navigate to its directory.
    ```

2.  **Install dependencies:**

    ```bash
    pip install requests rich cfonts user-agent AegosPy MedoSigner OneClick stdiomask
    ```

    *Note: `AegosPy` and `MedoSigner` are third-party libraries. Ensure they are compatible with your Python environment.* If you encounter permission errors during installation, try using `sudo pip install ...`.

## Usage

1.  **Run the script:**

    ```bash
    python3 merged_tiktok_tool.py
    ```

2.  **Enter your Telegram Bot ID and Token:**

    The script will prompt you to enter your Telegram `ID` and `Token`. These are used to send the results to your Telegram chat.

    *   **How to get your Telegram Bot Token**: Talk to BotFather on Telegram and create a new bot. It will give you a token.
    *   **How to get your Telegram Chat ID**: Forward any message from your chat to the `@getidsbot` on Telegram, and it will provide your chat ID.

3.  **The tool will start processing:**

    It will continuously search for TikTok users and check their email availability, sending successful finds to your Telegram bot.

## Important Notes

-   **Amazon Linux Compatibility**: The script is designed to run on Linux environments, including Amazon Linux, provided all Python dependencies are met.
-   **API Stability**: The tool relies on external APIs (livecounts.xyz, TikTok, AegosPy). Changes to these APIs may affect the tool's functionality.
-   **Rate Limiting**: Excessive requests might lead to IP bans or temporary blocks from the APIs. The script includes a random delay to mitigate this, but use responsibly.
-   **Error Handling**: Basic error handling is implemented, but comprehensive error logging and recovery might be needed for production use.
-   **`AegosPy` and `MedoSigner`**: These libraries are crucial for the tool's functionality. Ensure they are correctly installed and configured.

## Disclaimer

This tool is provided for educational and informational purposes only. The developer is not responsible for any misuse or consequences arising from the use of this tool. Ensure you comply with all applicable laws and terms of service of the platforms you interact with.
