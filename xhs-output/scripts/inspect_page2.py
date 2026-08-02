"""Inspect XHS publish page DOM using Playwright CDP."""
import asyncio, json, pprint
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # Connect to existing Chrome via CDP
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        
        # Find publish tab
        target_page = None
        for page in browser.contexts[0].pages if browser.contexts else []:
            pass  # Fall through
        
        # Just use the first context's default page
        context = browser.contexts[0]
        pages = context.pages
        target = None
        for pg in pages:
            if "publish" in pg.url:
                target = pg
                break
        if not target:
            target = pages[0] if pages else await context.new_page()
        
        # Navigate to publish page
        await target.goto("https://creator.xiaohongshu.com/publish/publish?source=official", wait_until="domcontentloaded")
        await asyncio.sleep(4)
        
        # Click 上传视频 tab
        try:
            tab_els = await target.query_selector_all("div.creator-tab")
            for tab_el in tab_els:
                text = await tab_el.text_content()
                if text and "上传视频" in text:
                    await tab_el.click()
                    print("Clicked 上传视频 tab")
                    await asyncio.sleep(2)
                    break
        except Exception as e:
            print(f"Tab click error: {e}")
        
        # Inspect title
        for sel in ['div.d-input input', 'input[placeholder*="标题"]', 'input.d-text']:
            el = await target.query_selector(sel)
            if el:
                info = await el.evaluate("""el => ({
                    tag: el.tagName,
                    type: el.getAttribute('type'),
                    placeholder: el.getAttribute('placeholder'),
                    visible: el.offsetParent !== null,
                    value: el.value,
                    id: el.id,
                    name: el.name,
                    className: el.className.substring(0, 100),
                    parentClass: el.parentElement?.className?.substring(0, 80)
                })""")
                print(f"\nTitle selector '{sel}':")
                pprint.pprint(info)
                break
            else:
                print(f"\nTitle selector '{sel}': NOT FOUND")
        
        # Inspect content editor
        for sel in ['div.tiptap.ProseMirror', 'div.ProseMirror[contenteditable="true"]', '[role="textbox"]', 'div.ql-editor']:
            el = await target.query_selector(sel)
            if el:
                info = await el.evaluate("""el => ({
                    tag: el.tagName,
                    role: el.getAttribute('role'),
                    contenteditable: el.getAttribute('contenteditable'),
                    visible: el.offsetParent !== null,
                    className: el.className.substring(0, 100),
                    placeholder: el.getAttribute('data-placeholder') || el.parentElement?.getAttribute('data-placeholder'),
                    parentTag: el.parentElement?.tagName,
                    parentRole: el.parentElement?.getAttribute('role'),
                    rect: JSON.stringify(el.getBoundingClientRect())
                })""")
                print(f"\nContent selector '{sel}':")
                pprint.pprint(info)
                break
            else:
                print(f"\nContent selector '{sel}': NOT FOUND")
        
        # List all data-placeholder
        info = await target.evaluate("""
            () => Array.from(document.querySelectorAll('[data-placeholder]')).map(el => ({
                tag: el.tagName,
                placeholder: el.getAttribute('data-placeholder'),
                parentRole: el.parentElement?.getAttribute('role'),
                parentTag: el.parentElement?.tagName,
                contenteditable: el.isContentEditable
            }))
        """)
        print("\nAll [data-placeholder] elements:")
        pprint.pprint(info)
        
        # List all input elements visible
        info2 = await target.evaluate("""
            () => {
                const all = document.querySelectorAll('input, textarea, [contenteditable="true"]');
                return Array.from(all).map(el => ({
                    tag: el.tagName,
                    type: el.getAttribute('type'),
                    placeholder: el.getAttribute('placeholder'),
                    visible: el.offsetParent !== null,
                    className: el.className.substring(0, 60),
                    role: el.getAttribute('role'),
                    contenteditable: el.getAttribute('contenteditable'),
                    rect: JSON.stringify(el.getBoundingClientRect())
                }));
            }
        """)
        print("\nAll input-like elements:")
        pprint.pprint(info2)
        
        await browser.close()

asyncio.run(main())
