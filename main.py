from quart import Quart, request, jsonify
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio

app = Quart(__name__)

async def scrape_clean_html(url, wait_selector='body'):
    async with async_playwright() as p:
        user_data_dir = "/tmp/playwright"
        context = await p.chromium.launch_persistent_context(
            user_data_dir,
            headless=True,
            args=["--no-sandbox"],
            locale="en-US",
            viewport={'width': 1280, 'height': 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/114.0.0.0 Safari/537.36"
            )
        )

        page = context.pages[0] if context.pages else await context.new_page()
        cleaned_content = ""

        try:
            await page.goto(url, timeout=60000, wait_until='domcontentloaded')
            try:
                await page.wait_for_selector(wait_selector, timeout=20000)
            except:
                await page.wait_for_selector("body", timeout=20000)

            await page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
            await asyncio.sleep(2)

            cleaned_content = await page.evaluate("""
                () => {
                    document.querySelectorAll('script, style, noscript, link, meta, iframe').forEach(el => el.remove());
                    return document.body.innerHTML;
                }
            """)
        except Exception as e:
            print("Scraping error:", e)
        finally:
            await context.close()

        return cleaned_content


@app.route('/scrape', methods=['POST'])
async def scrape_endpoint():
    data = await request.get_json()
    url = data.get("url")
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    wait_selector = 'a[href*="/news/"]' if "malaysiakini" in url else 'body'
    html = await scrape_clean_html(url, wait_selector)

    return jsonify({
        "url": url,
        "html": html,
        "status": "success" if html else "empty"
    })

# For Replit compatibility, bind to 0.0.0.0
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
