"""Quick DOM inspection of XHS publish page via existing Chrome CDP."""
import sys, json, time
sys.path.insert(0, r"D:\code\MyWord\.claude\skills\redbook-skills\scripts")
import cdp_publish

publisher = cdp_publish.XiaohongshuPublisher(host="127.0.0.1", port=9222)
publisher.connect()

# Navigate to publish page
result = publisher._evaluate("window.location.href")
print(f"Current URL: {result[:100] if result else 'None'}")

if not result or "publish" not in result:
    publisher._navigate("https://creator.xiaohongshu.com/publish/publish?source=official")

# Click 上传视频 tab
result = publisher._evaluate("""
    (() => {
        const tabs = document.querySelectorAll('div.creator-tab');
        for (const tab of tabs) {
            if (tab.textContent.includes('上传视频')) {
                tab.click();
                return 'CLICKED: 上传视频';
            }
        }
        return 'TABS: ' + Array.from(tabs).map(t => t.textContent.trim()).join(', ');
    })()
""")
print(f"Tab click: {result}")
time.sleep(3)

# Check video upload area
result = publisher._evaluate("""
    (() => {
        const info = {};
        
        // Title selectors
        info.title = {};
        const titleSels = ['div.d-input input', 'input[placeholder*="标题"]', 'input.d-text'];
        for (const sel of titleSels) {
            const el = document.querySelector(sel);
            info.title[sel] = el ? {
                tag: el.tagName,
                placeholder: el.getAttribute('placeholder'),
                visible: el.offsetParent !== null,
                value: el.value,
            } : null;
        }
        
        // Content selectors  
        info.content = {};
        const contentSels = ['div.tiptap.ProseMirror', 'div.ProseMirror', '[role="textbox"]', 'div.ql-editor'];
        for (const sel of contentSels) {
            const el = document.querySelector(sel);
            info.content[sel] = el ? {
                tag: el.tagName,
                role: el.getAttribute('role'),
                contenteditable: el.getAttribute('contenteditable'),
                visible: el.offsetParent !== null,
            } : null;
        }
        
        // All data-placeholder
        info.placeholders = Array.from(document.querySelectorAll('[data-placeholder]')).map(el => ({
            tag: el.tagName,
            text: el.getAttribute('data-placeholder'),
            visible: el.offsetParent !== null,
            parentTag: el.parentElement?.tagName,
            parentRole: el.parentElement?.getAttribute('role')
        }));
        
        // All visible inputs
        info.inputs = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"]')).filter(el => el.offsetParent !== null).map(el => ({
            tag: el.tagName,
            type: el.getAttribute('type'),
            placeholder: el.getAttribute('placeholder'),
            role: el.getAttribute('role'),
            contenteditable: el.getAttribute('contenteditable'),
        }));
        
        return info;
    })()
""")
print(f"\nDOM Inspection:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Also inspect the page body HTML structure
result2 = publisher._evaluate("""
    (() => {
        // Get the main upload area content
        const uploadArea = document.querySelector('.upload-area');
        const uploadInput = document.querySelector('.upload-input');
        
        // Get all major visible elements
        const mainContent = document.querySelector('main') || document.querySelector('[class*="content"]') || document.querySelector('.publish-page');
        
        return {
            uploadAreaExists: !!uploadArea,
            uploadInputExists: !!uploadInput,
            mainContentHTML: mainContent ? mainContent.innerHTML.substring(0, 2000) : 'no main content',
            bodyChildren: Array.from(document.body.children).slice(0, 10).map(el => ({
                tag: el.tagName,
                id: el.id,
                className: el.className.substring(0, 80),
                childCount: el.children.length
            })),
            // Check for any react root
            reactRoots: Array.from(document.querySelectorAll('#root, #__next, [data-reactroot]')).map(el => ({
                tag: el.tagName,
                id: el.id,
                innerHTML: el.innerHTML.substring(0, 500)
            }))
        };
    })()
""")
print(f"\nPage Structure:")
print(json.dumps(result2, indent=2, ensure_ascii=False))

publisher.disconnect()
