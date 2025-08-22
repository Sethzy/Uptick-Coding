Advanced Company Information Agent Prompt

Website:

Advanced Company Information Agent Prompt

Objective: Systematically navigate a company's website to intelligently identify, extract, and consolidate the maximum amount of key information into a structured JSON format. The agent will prioritize finding and scraping comprehensive details about the company, its products, and its pricing, ensuring a minimum of five pages are scraped for information. The final output for each page will be the raw, un-condensed content converted to Markdown.

Input:

company_name: The name of the company.

base_url: The root URL of the company's website (e.g., https://example.com).

Steps & Instructions:

Initial Scan & Prioritized Navigation:

Begin by navigating to the base_url.

Scan all visible links in the main navigation menu and the footer.

Prioritize links based on their text and semantic meaning. The agent's highest priority is to find pages that contain the following keywords, in order of importance:

about, company, who we are, our story

products, services, solutions, features, offerings

pricing, price, plans, cost

contact, support

careers, jobs

blog, news, media, press

sitemap

For each identified link, append it to a prioritized list of URLs to visit.

Information Extraction Logic (for each visited page):

For each page, capture the entire body of relevant content. Do not attempt to parse it into specific sub-fields (e.g., mission, history, etc.). Instead, convert the raw text and structure into a readable Markdown format. Use headings, bold text, lists, and other Markdown conventions to preserve the original page's structure and hierarchy.

Data Consolidation:

After scraping all identified pages, consolidate the extracted Markdown content into a single JSON object with a scrapedPages key that contains an array. Each object in the array will represent a scraped page.

Error Handling:

If a link or page is not found (e.g., a 404 error), log the error but continue to scrape the other available pages.

If a page's content doesn't match the expected structure, note this and extract as much relevant information as possible.

Output Format:

The final output must be a single, well-formatted JSON string that adheres to the following schema. Note that the pageName should be the URL slug of the page (e.g., "about-us", "our-products").

{ "scrapedPages": [ { "pageName": "about-us", "scrapedInformation": "## About Us

**Mission:** The company was founded in 1999 with a mission to revolutionize software development.

**History:** In 2005, we launched our flagship product.

**Values:** Innovation, Collaboration

**Leadership:** Jane Doe (CEO)" }, { "pageName": "products-services", "scrapedInformation": "## Products & Services

**Product A:** A powerful tool for data analysis with features like real-time dashboards and machine learning integrations.

**Product B:** A scalable cloud solution offering secure storage and fast retrieval." }, { "pageName": "pricing", "scrapedInformation": "## Pricing

**Starter Plan:** $25/month for up to 5 users.

**Pro Plan:** $100/month with unlimited users and advanced features.

**Enterprise Plan:** Custom pricing." }, { "pageName": "contact", "scrapedInformation": "## Contact

**Email:** info@example.com

**Phone:** (123) 456-7890

**Address:** 123 Main St, Anytown, USA." }, { "pageName": "careers", "scrapedInformation": "## Careers

**Open Positions:**

- Senior Software Engineer

- Product Manager

- UX Designer" } ] }
