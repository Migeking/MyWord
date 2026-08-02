"""Inspect XHS publish page DOM structure and test form filling."""
import urllib.request, json, time

def cdp_command(ws_url, method, params=None):
    import json, websocket
    ws = websocket.create_connection(ws_url, timeout=10)
    msg_id = 1
    cmd = json.dumps({"id": msg_id, "method": method, "params": params or {}})
    ws.send(cmd)
    resp = json.loads(ws.recv())
    ws.close()
    return resp.get("result")

# Find publish tab
pages = json.loads(urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=3).read().decode())
publish_pages = [p for p in pages if "xiaohongshu.com/publish" in p.get("url", "")]
if not publish_pages:
    print("No publish page tab found")
    for p in pages:
        print(f"  [{p['id']}] {p['url'][:100]}")
    exit(1)

tab = publish_pages[0]
ws_url = tab["webSocketDebuggerUrl"]
print(f"Connected to: {tab['url'][:100]}")

# Navigate to fresh publish page
cdp_command(ws_url, "Page.enable")
cdp_command(ws_url, "Page.navigate", {"url": "https://creator.xiaohongshu.com/publish/publish?source=official"})
time.sleep(3)

# Click "上传视频" tab first
cdp_command(ws_url, "Runtime.evaluate", {
    "expression": """
    (() => {
        const tabs = document.querySelectorAll('div.creator-tab');
        for (const tab of tabs) {
            if (tab.textContent.includes('上传视频')) {
                tab.click();
                return 'Clicked 上传视频 tab';
            }
        }
        return 'Tab not found';
    })()
    """,
    "returnByValue": True
})
time.sleep(2)

# Inspect the page structure
result = cdp_command(ws_url, "Runtime.evaluate", {
    "expression": """
    (() => {
        const info = {};
        
        // Check title input area
        const titleSelectors = [
            'div.d-input input',
            'input[placeholder*="标题"]',
            'input[placeholder*="填写标题"]',
            'input.d-text',
        ];
        info.title_selectors = {};
        for (const sel of titleSelectors) {
            const el = document.querySelector(sel);
            info.title_selectors[sel] = el ? {
                tag: el.tagName,
                type: el.getAttribute('type'),
                placeholder: el.getAttribute('placeholder'),
                visible: el.offsetParent !== null,
                value: el.value,
                className: el.className,
                parentClass: el.parentElement?.className
            } : null;
        }
        
        // Check content editor
        const contentSelectors = [
            'div.tiptap.ProseMirror',
            'div.ProseMirror[contenteditable="true"]',
            'div.ql-editor',
            '[role="textbox"]',
        ];
        info.content_selectors = {};
        for (const sel of contentSelectors) {
            const el = document.querySelector(sel);
            info.content_selectors[sel] = el ? {
                tag: el.tagName,
                role: el.getAttribute('role'),
                contenteditable: el.getAttribute('contenteditable'),
                visible: el.offsetParent !== null,
                className: el.className,
                innerHTML: el.innerHTML.substring(0, 100),
                rect: el.getBoundingClientRect()
            } : null;
        }
        
        // Check for data-placeholder elements
        info.placeholder_elements = [];
        const placeholders = document.querySelectorAll('[data-placeholder]');
        for (const el of placeholders) {
            info.placeholder_elements.push({
                tag: el.tagName,
                placeholder: el.getAttribute('data-placeholder'),
                parentRole: el.parentElement?.getAttribute('role')
            });
        }
        
        return info;
    })()
    """,
    "returnByValue": True
})

if result and "result" in result and "value" in result["result"]:
    import pprint
    pprint.pprint(result["result"]["value"])
else:
    print(f"No result: {result}")
