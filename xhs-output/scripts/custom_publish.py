import sys
import time
import json
sys.path.insert(0, 'scripts')

from cdp_publish import XiaohongshuPublisher

def run():
    pub = XiaohongshuPublisher()
    pub.connect()

    # Navigate to publish page
    print('[custom] Navigating to publish page...')
    pub._navigate('https://creator.xiaohongshu.com/publish/publish?source=official')
    time.sleep(3)

    # Click upload video tab
    print('[custom] Clicking upload video tab...')
    pub._click_tab('div.creator-tab, .creator-tab, [class*=creator-tab], [role=tab], button, div', '上传视频')
    time.sleep(2)

    # Upload video
    print('[custom] Uploading video...')
    pub._upload_video('D:\\code\\MyWord\\xhs-output\\鸿蒙工厂_1080p.mp4')

    # Wait for processing
    print('[custom] Waiting for video processing...')
    time.sleep(90)

    # Fill title
    print('[custom] Filling title...')
    pub._set_title('鸿蒙能帮工厂干什么？我亲眼看了100个案例后说实话')

    # Fill content
    print('[custom] Filling content...')
    with open('D:\\code\\MyWord\\xhs-output\\content.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    pub._set_content(content)

    time.sleep(5)

    # Check button state
    print('[custom] Checking publish button state...')
    result = pub._evaluate('''
    (() => {
        const selectors = [
            ".publish-page-publish-btn button.bg-red",
            "button.publishBtn",
            "button[class*=\"publish\"]",
            "[class*=\"publish-btn\"]",
            "button.bg-red",
            ".publish-page-publish-btn"
        ];
        for (const selector of selectors) {
            const button = document.querySelector(selector);
            if (button) {
                return JSON.stringify({
                    selector: selector,
                    found: true,
                    disabled: button.hasAttribute("disabled"),
                    className: button.className,
                    text: button.innerText,
                    rect: {x: button.getBoundingClientRect().x, y: button.getBoundingClientRect().y, w: button.getBoundingClientRect().width, h: button.getBoundingClientRect().height}
                });
            }
        }
        // Try finding by text
        const allButtons = document.querySelectorAll("button");
        for (const btn of allButtons) {
            if (btn.innerText.includes("发布")) {
                return JSON.stringify({
                    selector: "text:发布",
                    found: true,
                    disabled: btn.hasAttribute("disabled"),
                    className: btn.className,
                    text: btn.innerText,
                    rect: {x: btn.getBoundingClientRect().x, y: btn.getBoundingClientRect().y, w: btn.getBoundingClientRect().width, h: btn.getBoundingClientRect().height}
                });
            }
        }
        return JSON.stringify({found: false});
    })()
    ''')
    print('[custom] Button result:', result)

    # Try to get rect and click directly
    rect = pub._get_publish_button_rect()
    print('[custom] Button rect:', rect)

    if rect:
        print('[custom] Clicking at rect center...')
        cx = rect['x'] + rect['width'] / 2
        cy = rect['y'] + rect['height'] / 2
        pub._send("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": cx,
            "y": cy,
            "button": "left",
            "clickCount": 1
        })
        pub._send("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": cx,
            "y": cy,
            "button": "left",
            "clickCount": 1
        })
        print('[custom] Click sent!')
        time.sleep(5)

        # Check if we're on a new page or got an error
        current_url = pub._evaluate("window.location.href")
        print('[custom] Current URL:', current_url)
    else:
        print('[custom] Could not find publish button rect!')

run()