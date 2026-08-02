"""Inspect publish button state on Xiaohongshu publish page."""
import json, sys
sys.path.insert(0, "D:/code/MyWord/.claude/skills/redbook-skills")
from scripts.cdp_publish import XiaohongshuPublisher as CDPPublisher

p = CDPPublisher(headless=False)
p._sleep(3)

# Check URL
url = p._evaluate("window.location.href")
print("URL:", url)

# Find all buttons with publish text
result = p._evaluate("""
(() => {
    const all = document.querySelectorAll('button, [role="button"]');
    const found = [];
    for (const b of all) {
        const text = (b.innerText || '').trim();
        if (text.match(/\u53d1\u5e03|publish|\u786e\u8ba4/i)) {
            found.push({
                tag: b.tagName,
                id: b.id,
                className: String(b.className).substring(0, 120),
                text: text,
                disabled: b.hasAttribute('disabled'),
                visible: b.offsetParent !== null,
                w: b.getBoundingClientRect().width,
                h: b.getBoundingClientRect().height
            });
        }
    }
    return found;
})()
""")
print("Buttons with publish text:", json.dumps(result, ensure_ascii=False, default=str, indent=2))

# Check specific selector
sel1 = p._evaluate("document.querySelector('.publish-page-publish-btn button.bg-red') ? 'FOUND' : 'NOT FOUND'")
print("Selector .publish-page-publish-btn button.bg-red:", sel1)

sel2 = p._evaluate("document.querySelector('button.publishBtn') ? 'FOUND' : 'NOT FOUND'")
print("Selector button.publishBtn:", sel2)

# Dump all buttons for debugging
dump = p._evaluate("""
(() => {
    const btns = document.querySelectorAll('button');
    return Array.from(btns).slice(0, 20).map(b => ({
        text: (b.innerText || '').trim().substring(0, 30),
        cls: String(b.className).substring(0, 80),
        disabled: b.hasAttribute('disabled'),
        visible: b.offsetParent !== null
    }));
})()
""")
print("All buttons:", json.dumps(dump, ensure_ascii=False, indent=2))

p.close()
