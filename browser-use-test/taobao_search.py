"""
Browser Use + Playwright API 淘宝搜索演示
用 Browser Use 打开浏览器，Playwright 操作元素
"""
import asyncio
from browser_use import Browser

async def main():
    print("=" * 60)
    print("淘宝搜索：运动相机大疆")
    print("=" * 60)

    browser = Browser(headless=False)
    await browser.start()
    print("[OK] 浏览器已启动\n")

    try:
        # === 打开淘宝 ===
        print("1. 打开淘宝首页")
        await browser.navigate_to("https://www.taobao.com")
        await asyncio.sleep(2)

        # 获取 Playwright 的 Page 对象
        page = await browser.get_current_page()
        if not page:
            print("[FAIL] 无法获取页面对象")
            return

        title = await page.title()
        print(f"   页面标题: {title}")

        # === 搜索框输入 ===
        print("\n2. 搜索 \"运动相机大疆\"")
        await page.fill("input#q", "运动相机大疆")
        await asyncio.sleep(0.5)

        # 点击搜索按钮
        await page.click("button.btn-search")
        print("   已点击搜索按钮")

        # 等待搜索结果加载
        await asyncio.sleep(3)

        # === 截图结果 ===
        title = await page.title()
        print(f"\n3. 搜索结果页标题: {title}")

        await browser.take_screenshot("taobao_search_result.png")
        print("[OK] 截图已保存: taobao_search_result.png")

        # === 获取部分商品标题 ===
        print("\n4. 搜索结果预览:")
        items = await page.query_selector_all(".title--q4W2qkYr a")
        for i, item in enumerate(items[:5], 1):
            text = await item.inner_text()
            print(f"   [{i}] {text.strip()[:60]}")

        print("\n" + "=" * 60)
        print("完成！")
        print("=" * 60)

    finally:
        await browser.close()
        print("[OK] 浏览器已关闭")

if __name__ == "__main__":
    asyncio.run(main())
