import asyncio
import os
import json
import csv
from tools import web_search
from llm import batch_process_txt_files, save_processed_results, Result

places = [
    # "Osaka",
    # "Kyoto",
    # "Nara",
    # "Kobe",
    # "Otsu",
    # "Takatsuki",
    # "Awaji Island",
    # "Okayama",
    # "Himeji",
    # "Kurashiki",
    # "Fukuyama",
    # "Takamatsu",
    # "Kanazawa",
    # "Nagoya",
    # "Toyota",
    # "Okazaki",
    # "Toyohashi",
    # "Gifu",
    # "Shiga",

    "Hakone",
]

queries = [
    "Things to do in Japan {place}",
    "Places to visit in Japan {place}",
    "Parks to visit at Japan {place}",
    "Restaurants to visit at Japan {place}",
    "Hotels to visit at Japan {place}",
    "Attractions to visit at Japan {place}",
    "Festivals to visit at Japan {place}",
    "Events to visit at Japan {place}",
    "Shopping to visit at Japan {place}",
    "Nightlife to visit at Japan {place}",
    "Cafes to visit at Japan {place}",
    "Bars to visit at Japan {place}",
    "Museum to visit at Japan {place}",
    "Art galleries to visit at Japan {place}",
    "Craft stores to visit at Japan {place}",
    "Local food to visit at Japan {place}",
    "Local art to visit at Japan {place}",
]

results = []

# File to track visited URLs
visited_urls_file = "visited_urls.txt"


def load_visited_urls():
    """Load the set of already visited URLs"""
    if os.path.exists(visited_urls_file):
        with open(visited_urls_file, 'r', encoding='utf-8') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_visited_url(url):
    """Save a URL to the visited URLs file"""
    with open(visited_urls_file, 'a', encoding='utf-8') as f:
        f.write(f"{url}\n")


async def scrape_data():
    """Original web scraping functionality"""
    # Load already visited URLs
    visited_urls = load_visited_urls()
    print(f"Loaded {len(visited_urls)} previously visited URLs")

    for place in places:
        # Create folder for the place in data/ directory
        place_folder = os.path.join("data", place.lower().replace(" ", "_"))
        os.makedirs(place_folder, exist_ok=True)

        print(f"Processing {place}...")

        # Counter for file naming
        file_counter = 1

        for query_template in queries:
            query = query_template.format(place=place)
            print(f"  Searching: {query}")

            try:
                result = await web_search(query, n=10)

                # Save each website content as numbered .txt files
                for website_data in result:
                    # Skip if URL already visited
                    if website_data['url'] in visited_urls:
                        print(
                            f"    Skipping already visited URL: {website_data['url']}")
                        continue

                    filename = f"{file_counter}.txt"
                    filepath = os.path.join(place_folder, filename)

                    # Create content with title, URL, and content
                    content = f"Title: {website_data['title']}\n"
                    content += f"URL: {website_data['url']}\n"
                    content += f"Query: {query}\n"
                    content += f"Content:\n{website_data['content']}\n"

                    # Save to file
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                    # Mark URL as visited
                    save_visited_url(website_data['url'])
                    visited_urls.add(website_data['url'])

                    print(f"    Saved {filename} for {place}")
                    file_counter += 1

            except Exception as e:
                print(f"    Error processing query '{query}': {e}")
                continue

        print(f"Completed {place}\n")


async def main():
    """Main function to run the complete pipeline"""
    print("=== Japan Travel Data Processing Pipeline ===\n")

    # Step 1: Scrape data
    # await scrape_data()

    # # Step 1: Check if we need to scrape data
    # data_files = []
    # for place in places:
    #     place_folder = os.path.join("data", place.lower().replace(" ", "_"))
    #     if os.path.exists(place_folder):
    #         place_files = [f for f in os.listdir(
    #             place_folder) if f.endswith('.txt')]
    #         data_files.extend([os.path.join(place_folder, f)
    #                           for f in place_files])

    # if not data_files:
    #     print("No existing data files found. Starting web scraping...")
    #     await scrape_data()
    # else:
    #     print(
    #         f"Found {len(data_files)} existing data files. Skipping web scraping.")

    # Step 2: Process all .txt files with LLM and write to CSV incrementally
    print("\n=== Starting LLM Processing ===")
    results = await batch_process_txt_files(model="gpt-4.1", max_concurrent=50, csv_file="master_list.csv")

    # Step 3: Save JSON results
    await save_processed_results(results)

    # Step 4: Print summary
    total_results = sum(len(result_list.results)
                        for result_list in results.values())
    print(f"\n=== Processing Complete ===")
    print(f"Processed {len(results)} files")
    print(f"Extracted {total_results} total results")
    print(f"Master CSV updated incrementally: master_list.csv")


if __name__ == "__main__":
    asyncio.run(main())
