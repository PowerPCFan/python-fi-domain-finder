import asyncio
import time
import httpx
from pathlib import Path


ANSI = "\033["
GREEN = ANSI + "32m"
RESET = ANSI + "0m"


retry_storage: dict[str, int] = {}
available: dict[int, list[str]] = {}


def check_availability(session: httpx.Client, domain: str) -> bool:
    print(f"\nChecking domain '{domain}'...")

    response = session.post(
        "https://www.domainhotelli.fi/asiakkaat/modules/addons/ispapidomaincheck/domain_search_wrapper_cnic.php",
        data={ "domain": domain, "domains[]": domain },
    )

    if response.status_code != 200:
        if response.status_code == 429:
            retry_storage[domain] = retry_storage.get(domain, 0) + 1
            if retry_storage[domain] > 3:
                print(f"Rate limited too many times for '{domain}'. Skipping.")
                return False

            retry_after = int(response.headers.get("Retry-After", 1))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            return check_availability(session, domain)
        else:
            print(f"Error: domainhotelli.fi returned {response.status_code}")
            return False

    if "available" in response.text:
        print(f"{GREEN}'{domain}' is available!{RESET}")
        return True

    print(f"'{domain}' is not available.")
    return False


def write(words: list[str], path: str) -> None:
    with Path(path).open("w") as f:
        f.write("\n".join(words))


def search(words: list[str]) -> list[str]:
    with httpx.Client(timeout=5) as client:
        return [word for word in words if check_availability(client, word.replace('-', '').strip() + ".fi")]


def main():
    raw_path = input("Newline-separated word list path: ")
    word_list_path = Path(raw_path)
    if not word_list_path.exists() or not word_list_path.is_file():
        print("File does not exist or is not a file.")
        return

    word_length = int(input("Domain length (excluding TLD): "))
    raw_words = [word for word in [line.strip() for line in word_list_path.read_text().splitlines()] if word]
    words = [word for word in raw_words if len(word) == word_length]

    if len(words) < 10:
        print("Not enough words to check. Please provide at least 10 words of the specified length.")
        return

    print(f"Words that fit the word length: {len(words)} (out of {len(raw_words)} total words)")
    print("Checking for domains...")

    word_chunks: dict[int, list[str]] = {}
    for i, word in enumerate(words):
        chunk_index = i % 10
        if chunk_index not in word_chunks:
            word_chunks[chunk_index] = []
        word_chunks[chunk_index].append(word)

    for i in range(10):
        avail = asyncio.run(asyncio.to_thread(search, word_chunks[i]))
        available[i] = avail

    combined = []
    for domains in available.values():
        for domain in domains:
            combined.append(domain)

    sorted_with_tld = [domain + ".fi" for domain in sorted(combined)]
    write(sorted_with_tld, "available.txt")

    print("Done! Saved to available.txt")

if __name__ == "__main__":
    main()
