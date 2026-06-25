import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx


ANSI = "\033["
GREEN = ANSI + "32m"
RESET = ANSI + "0m"

URL = "https://www.domainhotelli.fi/asiakkaat/modules/addons/ispapidomaincheck/domain_search_wrapper_cnic.php"


def check_availability(domain: str) -> bool:
    print(f"\nChecking domain '{domain}'...")

    with httpx.Client(timeout=10) as client:
        for attempt in range(1, 4):
            try:
                response = client.post(
                    URL,
                    data={"domain": domain, "domains[]": domain},
                )
            except httpx.HTTPError as error:
                print(f"Request failed for '{domain}': {error}")
                return False

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 1))
                print(f"Rate limited for '{domain}'. Retrying after {retry_after} seconds...")
                time.sleep(retry_after)
                continue

            if response.status_code != 200:
                print(f"Error: domainhotelli.fi returned {response.status_code} for '{domain}'")
                return False

            if "available" in response.text:
                print(f"{GREEN}'{domain}' is available!{RESET}")
                return True

            print(f"'{domain}' is not available.")
            return False

    print(f"Rate limited too many times for '{domain}'. Skipping.")
    return False


def write(domains: list[str], path: str) -> None:
    Path(path).write_text("\n".join(domains))


def check_word(word: str) -> str | None:
    domain = word.replace("-", "").strip() + ".fi"
    if check_availability(domain):
        return domain
    return None


def main():
    raw_path = input("Newline-separated word list path: ")
    word_list_path = Path(raw_path)
    if not word_list_path.exists() or not word_list_path.is_file():
        print("File does not exist or is not a file.")
        return

    try:
        word_length = int(input("Domain length excluding TLD, or 0 for any: "))
    except ValueError:
        print("Invalid word length.")
        return

    try:
        max_workers = int(input("How many requests can be active at a time? Default 5: ") or "5")
    except ValueError:
        print("Invalid maximum connections.")
        return

    raw_words = [line.strip() for line in word_list_path.read_text().splitlines() if line.strip()]

    if word_length == 0:
        words = raw_words
    else:
        words = [word for word in raw_words if len(word) == word_length]

    print(f"Words that fit the word length: {len(words)} (out of {len(raw_words)} total words)")
    print("Checking for domains...")

    found_domains: list[str] = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(check_word, word)
            for word in words
        ]

        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                found_domains.append(result)

    save_name = f"available_{int(time.time())}.txt"
    write(sorted(found_domains), save_name)

    print(f"Done! Saved to {save_name}")

if __name__ == "__main__":
    main()
