"""
测试 Browser Use 底层浏览器功能（不依赖 LLM）
验证 Playwright / CDP 集成是否正常
"""
import asyncio
from browser_use import Browser

async def test_browser():
    print("=" * 60)
    print("Browser Use 底层浏览器功能测试")
    print("=" * 60)
    
    browser = Browser(headless=False)
    print("[✓] 浏览器实例创建成功")
    
    try:
        await browser.start()
        print("[✓] 浏览器已启动")
        
        await browser.navigate_to("https://www.baidu.com")
        print("[✓] 导航到 baidu.com 完成")
        
        title = await browser.get_current_page_title()
        url = await browser.get_current_page_url()
        print(f"    URL:  {url}")
        print(f"    标题: {title}")
        
        screenshot = await browser.take_screenshot()
        print(f"[✓] 截图成功 ({len(screenshot)} bytes)")
        
        print("\n[✓] 浏览器功能测试全部通过！")
        return True
        
    except Exception as e:
        print(f"\n[✗] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await browser.close()
        print("[✓] 浏览器已关闭")

async def main():
    result = await test_browser()
    print(f"\n{'='*60}")
    print(f"最终结果: {'[✓] 通过' if result else '[✗] 失败'}")

if __name__ == "__main__":
    asyncio.run(main())
