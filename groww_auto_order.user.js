// ==UserScript==
// @name         Groww Quant Auto-Order Bridge
// @namespace    http://localhost:8080/
// @version      1.2
// @description  Automatically fills Quantity and Stop Loss from your Quant Terminal into Groww
// @author       Antigravity
// @match        https://groww.in/*
// @match        https://*.groww.in/*
// @grant        GM_xmlhttpRequest
// @connect      localhost
// @connect      127.0.0.1
// @connect      test-admin.housiey.com
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';
    console.log("[Quant Userscript] Groww Auto-Order active.");

    function setReactInputValue(inputElement, value) {
        if (!inputElement) return false;
        try {
            inputElement.focus();
            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
            if (nativeSetter) {
                nativeSetter.call(inputElement, value);
            } else {
                inputElement.value = value;
            }
            inputElement.dispatchEvent(new Event('input', { bubbles: true, cancelable: true }));
            inputElement.dispatchEvent(new Event('change', { bubbles: true, cancelable: true }));
            inputElement.dispatchEvent(new KeyboardEvent('keydown', { key: value.toString().slice(-1), bubbles: true }));
            inputElement.dispatchEvent(new KeyboardEvent('keypress', { key: value.toString().slice(-1), bubbles: true }));
            inputElement.dispatchEvent(new KeyboardEvent('keyup', { key: value.toString().slice(-1), bubbles: true }));
            inputElement.dispatchEvent(new Event('blur', { bubbles: true }));
            return true;
        } catch (e) {
            console.error(e);
            return false;
        }
    }

    function findGrowwQuantityInput() {
        const allInputs = Array.from(document.querySelectorAll("input")).filter(inp => {
            const placeholder = (inp.placeholder || "").toLowerCase();
            const id = (inp.id || "").toLowerCase();
            const type = (inp.type || "").toLowerCase();
            return !placeholder.includes("search") && id !== "globalsearch23" && type !== "hidden" && type !== "checkbox";
        });

        const allLabels = Array.from(document.querySelectorAll("div, span, p, label"));
        const qtyLabel = allLabels.find(el => {
            const txt = (el.innerText || "").trim().toUpperCase();
            return txt.startsWith("QTY NSE") || txt.startsWith("QTY BSE") || txt === "QTY";
        });

        if (qtyLabel) {
            let parent = qtyLabel.parentElement;
            for (let i = 0; i < 4; i++) {
                if (!parent) break;
                const inp = parent.querySelector("input");
                if (inp && !inp.placeholder?.toLowerCase().includes("search")) {
                    return inp;
                }
                parent = parent.parentElement;
            }
        }

        if (allInputs.length > 0) return allInputs[0];
        return null;
    }

    function tryFillStoplossAndTarget(slPrice) {
        if (!slPrice) return;
        const allTexts = Array.from(document.querySelectorAll("div, span, a, p"));
        const slLink = allTexts.find(el => {
            const t = (el.innerText || "").trim().toLowerCase();
            return t.includes("add stoploss") || t.includes("stoploss / target");
        });

        if (slLink) {
            slLink.click();
            setTimeout(() => {
                const inputs = Array.from(document.querySelectorAll("input")).filter(inp => {
                    const placeholder = (inp.placeholder || "").toLowerCase();
                    return !placeholder.includes("search");
                });
                if (inputs.length >= 2 && slPrice) {
                    const slInput = inputs.find(inp => {
                        const p = (inp.placeholder || "").toLowerCase();
                        const id = (inp.id || "").toLowerCase();
                        return p.includes("trigger") || p.includes("stop") || id.includes("stop") || id.includes("trigger");
                    }) || inputs[1];
                    if (slInput) setReactInputValue(slInput, slPrice);
                }
            }, 400);
        }
    }

    function showQuantHUD(message) {
        let banner = document.getElementById("quant-hud-banner");
        if (!banner) {
            banner = document.createElement("div");
            banner.id = "quant-hud-banner";
            banner.style.cssText = `
                position: fixed;
                top: 24px;
                right: 24px;
                z-index: 99999999;
                padding: 16px 22px;
                border-radius: 14px;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 14px;
                font-weight: 700;
                box-shadow: 0 12px 30px rgba(0,0,0,0.45);
                transition: all 0.35s ease;
                display: flex;
                align-items: center;
                gap: 12px;
                background: linear-gradient(135deg, #059669, #047857);
                color: #ffffff;
                border: 1px solid rgba(16, 185, 129, 0.5);
            `;
            document.body.appendChild(banner);
        }
        banner.innerHTML = `<span style="font-size:18px;">⚡</span> <div>${message}</div>`;
        banner.style.opacity = "1";
        banner.style.transform = "translateY(0)";
        setTimeout(() => {
            banner.style.opacity = "0";
            banner.style.transform = "translateY(-12px)";
        }, 7000);
    }

    function executeAutoPopulate(order) {
        let attempts = 0;
        const timer = setInterval(() => {
            attempts++;
            const qtyInput = findGrowwQuantityInput();
            if (qtyInput) {
                clearInterval(timer);
                setReactInputValue(qtyInput, order.quantity);
                if (order.stop_loss) tryFillStoplossAndTarget(order.stop_loss);

                showQuantHUD(`
                    <div style="font-size:15px; font-weight:800;">Order Ready: ${order.quantity} Shares (${order.name})</div>
                    <div style="font-size:12px; opacity:0.9;">Amount: ₹${order.invested_amount || '-'} | SL: ₹${order.stop_loss || '-'}</div>
                    <div style="font-size:11px; color:#a7f3d0; margin-top:3px;">👉 Fields populated! Review and click BUY.</div>
                `);
            } else if (attempts >= 25) {
                clearInterval(timer);
            }
        }, 200);
    }

    const params = new URLSearchParams(window.location.search);
    if (params.get("quant_action") === "buy") {
        executeAutoPopulate({
            quantity: params.get("qty"),
            name: params.get("name") || "Stock",
            stop_loss: params.get("sl"),
            target: params.get("target"),
            invested_amount: params.get("amount")
        });
    }
})();
