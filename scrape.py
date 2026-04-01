import asyncio
import json
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, BFSDeepCrawlStrategy


async def main():
    strategy = BFSDeepCrawlStrategy(
        max_depth=3,
        include_external=False,
    )
    config = CrawlerRunConfig(
        deep_crawl_strategy=strategy,
        word_count_threshold=50,
        verbose=True,
    )

    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun(url="https://docs.mostly.ai/", config=config)

    pages = []
    # arun with deep crawl returns a list of CrawlResult
    if isinstance(results, list):
        all_results = results
    else:
        all_results = [results]

    for result in all_results:
        if not result.success:
            continue
        markdown = result.markdown or ""
        if len(markdown.split()) < 50:
            continue
        title = result.metadata.get("title", "") if result.metadata else ""
        pages.append({
            "url": result.url,
            "title": title,
            "markdown": markdown,
        })

    with open("pages.json", "w", encoding="utf-8") as f:
        json.dump(pages, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(pages)} pages to pages.json")


asyncio.run(main())
