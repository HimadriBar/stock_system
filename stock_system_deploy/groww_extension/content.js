/**
 * Groww Quant Auto-Order Bridge & High-Safety Notification Engine
 * - Automatically fills Quantity and Stop Loss on Groww stock order card
 * - Supports React 17/18 state tracker preservation
 * - Polls backend bridge for pending orders and 90%+ high-safety alerts
 * - Listens to SPA route changes
 */

console.log("[Quant Bridge] Groww Auto-Order & Safety Alert Script initialized.");

const SERVER_ENDPOINTS = [
    "http://localhost:9012",
    "http://127.0.0.1:9012",
    "https://test-admin.housiey.com"
];

let lastHandledOrderId = 0;
let lastNotifiedStockTicker = "";
let currentUrl = window.location.href;

// Robust React 16/17/18 input state updater
function setReactInputValue(input, val) {
    if (!input || val === undefined || val === null) return false;
    try {
        input.focus();
        const lastValue = input.value;
        input.value = val;
        
        // Preserve React 16-18 internal value tracker
        const tracker = input._valueTracker;
        if (tracker) {
            tracker.setValue(lastValue);
        }

        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value')?.set;
        if (nativeSetter) {
            nativeSetter.call(input, val);
        }

        input.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
        input.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
        input.dispatchEvent(new KeyboardEvent('keydown', { key: val.toString().slice(-1), bubbles: true }));
        input.dispatchEvent(new KeyboardEvent('keyup', { key: val.toString().slice(-1), bubbles: true }));
        input.dispatchEvent(new Event('blur', { bubbles: true }));
        return true;
    } catch (e) {
        console.error("[Quant Bridge] Error setting input value:", e);
        return false;
    }
}

// Multi-strategy Quantity input locator
function findQuantityInput() {
    // 1. Direct ID check (for mock / standard Groww forms)
    const directId = document.getElementById("qty-input") || document.getElementById("quantity");
    if (directId) return directId;

    // 2. Proximity search around labels ("Qty NSE", "Qty BSE", "Shares", "Quantity")
    const allLabels = Array.from(document.querySelectorAll('div, span, p, label'));
    for (const el of allLabels) {
        const txt = (el.innerText || el.textContent || '').trim().toUpperCase();
        if (txt === 'QTY NSE' || txt === 'QTY BSE' || txt.startsWith('QTY') || txt === 'SHARES' || txt === 'QUANTITY') {
            let parent = el.parentElement;
            for (let d = 0; d < 5 && parent; d++) {
                const inp = parent.querySelector('input');
                if (inp && inp.id !== 'globalSearch23' && inp.type !== 'hidden') {
                    return inp;
                }
                parent = parent.parentElement;
            }
        }
    }

    // 3. Fallback: First visible non-search input on page
    const inputs = Array.from(document.querySelectorAll('input')).filter(i => {
        const ph = (i.placeholder || '').toLowerCase();
        const id = (i.id || '').toLowerCase();
        const type = (i.type || '').toLowerCase();
        return !ph.includes('search') && id !== 'globalsearch23' && type !== 'hidden' && type !== 'checkbox';
    });
    return inputs[0] || null;
}

// Find and trigger Stop Loss input
function clickAddStoploss() {
    const allNodes = Array.from(document.querySelectorAll('div, span, a, p, button'));
    for (const node of allNodes) {
        const t = (node.innerText || node.textContent || '').trim().toLowerCase();
        if (t.includes('add stoploss') || t.includes('stoploss / target') || t.includes('stoploss')) {
            node.click();
            if (node.parentElement) node.parentElement.click();
            return true;
        }
    }
    return false;
}

function runAutoFill(qty, sl, stockName) {
    console.log(`[Quant Bridge] Auto-filling parameters: Qty=${qty}, SL=${sl}, Stock=${stockName}`);
    
    // Fill Quantity
    const qtyInput = findQuantityInput();
    if (qtyInput) {
        setReactInputValue(qtyInput, qty);
        console.log(`[Quant Bridge] Quantity successfully set to ${qty}`);
    }

    // Click Stoploss trigger
    if (sl) {
        clickAddStoploss();
        setTimeout(() => {
            const inputs = Array.from(document.querySelectorAll('input')).filter(i => {
                const ph = (i.placeholder || '').toLowerCase();
                const id = (i.id || '').toLowerCase();
                return !ph.includes('search') && id !== 'globalsearch23' && i.type !== 'hidden';
            });

            // Target Stoploss price input
            const slInput = inputs.find(inp => {
                const p = (inp.placeholder || '').toLowerCase();
                const id = (inp.id || '').toLowerCase();
                return p.includes('trigger') || p.includes('stop') || id.includes('stop') || id.includes('sl');
            }) || (inputs.length >= 2 ? inputs[1] : null);

            if (slInput) {
                setReactInputValue(slInput, sl);
                console.log(`[Quant Bridge] Stop Loss set to ${sl}`);
            }
        }, 350);
    }

    showHUD(`⚡ Order Populated: <strong>${qty} Shares</strong> of <strong>${stockName || 'Stock'}</strong> (SL: ₹${sl || '-'}). Click BUY to execute!`);
}

function showHUD(message, isAlert = false) {
    let hud = document.getElementById("quant-order-hud");
    if (!hud) {
        hud = document.createElement("div");
        hud.id = "quant-order-hud";
        hud.style.cssText = `
            position: fixed;
            bottom: 30px;
            right: 30px;
            z-index: 99999999;
            color: #ffffff;
            padding: 16px 22px;
            border-radius: 12px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
            font-weight: 700;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.3s ease;
        `;
        document.body.appendChild(hud);
    }

    hud.style.background = isAlert ? "linear-gradient(135deg, #b91c1c, #991b1b)" : "linear-gradient(135deg, #059669, #047857)";
    hud.style.border = isAlert ? "1px solid #f87171" : "1px solid #10b981";
    hud.innerHTML = `<span>${isAlert ? '🚨' : '⚡'}</span> <div>${message}</div>`;
    hud.style.opacity = "1";
    hud.style.transform = "translateY(0)";

    setTimeout(() => {
        hud.style.opacity = "0";
        hud.style.transform = "translateY(10px)";
    }, isAlert ? 10000 : 7000);
}

// Injects a floating helper button directly on Groww for instant 1-click execution
function injectQuickFillButton(qty, sl) {
    if (document.getElementById("btn-quick-fill-quant")) return;

    const btn = document.createElement("button");
    btn.id = "btn-quick-fill-quant";
    btn.innerHTML = `⚡ Fill Quant Order (${qty || 1} Qty | SL: ₹${sl || '-'})`;
    btn.style.cssText = `
        position: fixed;
        top: 80px;
        right: 25px;
        z-index: 9999999;
        background: #00d09c;
        color: #022c1b;
        font-weight: 800;
        font-size: 13px;
        padding: 10px 18px;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 208, 156, 0.4);
        transition: transform 0.2s;
    `;
    btn.onmouseover = () => btn.style.transform = "scale(1.05)";
    btn.onmouseout = () => btn.style.transform = "scale(1)";
    btn.onclick = () => {
        runAutoFill(qty, sl);
        btn.innerHTML = "✅ Filled! Click Buy";
        btn.style.background = "#059669";
        btn.style.color = "#fff";
    };
    document.body.appendChild(btn);
}

// Polling background bridge for pending orders and 90%+ high safety notifications
async function pollBridgeServer() {
    for (const host of SERVER_ENDPOINTS) {
        try {
            // 1. Check for Pending Order
            const orderRes = await fetch(`${host}/api/pending-order`, { signal: AbortSignal.timeout(1500) });
            if (orderRes.ok) {
                const orderData = await orderRes.json();
                if (orderData && orderData.order && orderData.order_id > lastHandledOrderId) {
                    lastHandledOrderId = orderData.order_id;
                    const o = orderData.order;
                    const path = window.location.pathname;

                    // If user is currently on that stock's page, auto-fill directly
                    if (!o.slug || path.includes(o.slug)) {
                        runAutoFill(o.quantity, o.stop_loss, o.name);
                        fetch(`${host}/api/clear-pending-order`, { method: 'POST' }).catch(() => {});
                    } else {
                        // Prompt user to navigate to that stock
                        showHUD(`Order received for <strong>${o.name}</strong> (${o.quantity} shares). <a href="/stocks/${o.slug}?quant_action=buy&qty=${o.quantity}&name=${encodeURIComponent(o.name)}&sl=${o.stop_loss}" style="color:#a7f3d0; text-decoration:underline;">Click here to open & fill</a>`);
                    }
                }
            }

            // 2. Check for 90%+ High-Safety Notifications
            const notifRes = await fetch(`${host}/api/notifications`, { signal: AbortSignal.timeout(1500) });
            if (notifRes.ok) {
                const notifData = await notifRes.json();
                const alerts = notifData.alerts || [];
                if (alerts.length > 0) {
                    const topAlert = alerts[0];
                    if (topAlert.ticker !== lastNotifiedStockTicker) {
                        lastNotifiedStockTicker = topAlert.ticker;
                        showHUD(`🚨 <strong>90%+ HIGH SAFETY ALERT:</strong> ${topAlert.name} has crossed <strong>${topAlert.safe_percentage}% Safe Score</strong>! <a href="/stocks/${topAlert.slug}?quant_action=buy&qty=1&name=${encodeURIComponent(topAlert.name)}" style="color:#fecaca; text-decoration:underline; margin-left:6px;">View Stock</a>`, true);
                    }
                }
            }
            break; // Stop after first reachable host
        } catch (e) {
            // Try next host
        }
    }
}

// Main bootstrap loop
function init() {
    const urlParams = new URLSearchParams(window.location.search);
    const hashParams = new URLSearchParams(window.location.hash.replace('#', '?'));
    
    const qty = urlParams.get('qty') || hashParams.get('qty');
    const sl = urlParams.get('sl') || hashParams.get('sl');
    const name = urlParams.get('name') || hashParams.get('name') || 'Stock';

    if (qty) {
        let attempts = 0;
        const interval = setInterval(() => {
            attempts++;
            const qtyInput = findQuantityInput();
            if (qtyInput) {
                clearInterval(interval);
                runAutoFill(qty, sl, name);
                injectQuickFillButton(qty, sl);
            } else if (attempts >= 30) {
                clearInterval(interval);
                injectQuickFillButton(qty, sl);
            }
        }, 200);
    }
}

// Observe SPA navigation (Next.js route changes without page reload)
function setupSpaNavigationObserver() {
    const handleUrlChange = () => {
        if (window.location.href !== currentUrl) {
            currentUrl = window.location.href;
            console.log("[Quant Bridge] Detected SPA URL navigation to:", currentUrl);
            setTimeout(init, 300);
        }
    };

    window.addEventListener('popstate', handleUrlChange);

    const origPushState = history.pushState;
    history.pushState = function() {
        origPushState.apply(this, arguments);
        handleUrlChange();
    };

    const origReplaceState = history.replaceState;
    history.replaceState = function() {
        origReplaceState.apply(this, arguments);
        handleUrlChange();
    };
}

// Run on load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        init();
        setupSpaNavigationObserver();
    });
} else {
    init();
    setupSpaNavigationObserver();
}

// Start periodic bridge polling every 3 seconds
setInterval(pollBridgeServer, 3000);
