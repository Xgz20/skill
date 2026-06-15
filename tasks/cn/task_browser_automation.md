---
id: task_browser_automation
name: 浏览器自动化工作流
category: 编程
scene: 本地环境、命令执行与脚本任务
sub_scene: 浏览器自动化测试
difficulty: L2
capabilities:
- 代码生成与理解
- 指令遵循与约束理解
- 多步推理
- 工具调用
- 输出格式适配
grading_type: hybrid
timeout_seconds: 180
workspace_files:
  - path: "shop.html"
    content: |
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>TechMart — Gadget Shop</title>
        <style>
          * { box-sizing: border-box; margin: 0; padding: 0; font-family: system-ui, sans-serif; }
          body { background: #f5f5f5; padding: 20px; }
          h1 { text-align: center; margin-bottom: 20px; color: #333; }
          .products { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 16px; max-width: 900px; margin: 0 auto 20px; }
          .product { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
          .product h3 { margin-bottom: 8px; }
          .product .price { color: #16a34a; font-weight: bold; font-size: 1.2em; }
          .product .stock { color: #666; font-size: .85em; margin: 4px 0 12px; }
          .product button { background: #2563eb; color: #fff; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; }
          .product button:disabled { background: #9ca3af; cursor: not-allowed; }
          .product button:hover:not(:disabled) { background: #1d4ed8; }
          #cart { max-width: 900px; margin: 0 auto; background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
          #cart h2 { margin-bottom: 12px; }
          #cart-items { list-style: none; }
          #cart-items li { display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }
          #cart-items li .remove { color: #dc2626; cursor: pointer; text-decoration: underline; }
          #total { font-weight: bold; font-size: 1.1em; margin-top: 12px; }
          #checkout { margin-top: 12px; background: #16a34a; color: #fff; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 1em; }
          #checkout:hover { background: #15803d; }
          #checkout:disabled { background: #9ca3af; cursor: not-allowed; }
          #order-confirmation { display: none; max-width: 900px; margin: 20px auto; padding: 20px; background: #dcfce7; border-radius: 8px; text-align: center; }
          #order-confirmation h2 { color: #16a34a; }
          #order-id { font-family: monospace; font-size: 1.2em; }
        </style>
      </head>
      <body>
        <h1>TechMart — Gadget Shop</h1>
        <div class="products" id="product-list"></div>
        <div id="cart">
          <h2>Shopping Cart</h2>
          <ul id="cart-items"></ul>
          <div id="total">Total: $0.00</div>
          <button id="checkout" disabled>Checkout</button>
        </div>
        <div id="order-confirmation">
          <h2>Order Confirmed!</h2>
          <p>Your order <span id="order-id"></span> has been placed.</p>
          <p id="order-summary"></p>
        </div>
        <script>
          const products = [
            { id: 1, name: "Wireless Mouse", price: 29.99, stock: 15 },
            { id: 2, name: "Mechanical Keyboard", price: 89.99, stock: 8 },
            { id: 3, name: "USB-C Hub", price: 45.00, stock: 23 },
            { id: 4, name: "Webcam HD 1080p", price: 59.99, stock: 0 },
            { id: 5, name: "Monitor Stand", price: 34.50, stock: 12 },
            { id: 6, name: "Laptop Sleeve 15\"", price: 24.99, stock: 30 },
          ];
          let cart = [];
          function renderProducts() {
            const el = document.getElementById("product-list");
            el.innerHTML = products.map(p => `
              <div class="product" data-id="${p.id}">
                <h3>${p.name}</h3>
                <div class="price">$${p.price.toFixed(2)}</div>
                <div class="stock">${p.stock > 0 ? p.stock + " in stock" : "Out of stock"}</div>
                <button onclick="addToCart(${p.id})" ${p.stock === 0 ? "disabled" : ""}>Add to Cart</button>
              </div>
            `).join("");
          }
          function addToCart(id) {
            const p = products.find(x => x.id === id);
            if (!p || p.stock <= 0) return;
            const existing = cart.find(x => x.id === id);
            if (existing) { existing.qty++; } else { cart.push({ ...p, qty: 1 }); }
            p.stock--;
            renderProducts();
            renderCart();
          }
          function removeFromCart(id) {
            const idx = cart.findIndex(x => x.id === id);
            if (idx === -1) return;
            const item = cart[idx];
            const p = products.find(x => x.id === id);
            p.stock += item.qty;
            cart.splice(idx, 1);
            renderProducts();
            renderCart();
          }
          function renderCart() {
            const el = document.getElementById("cart-items");
            el.innerHTML = cart.map(item => `
              <li>
                <span>${item.name} × ${item.qty}</span>
                <span>$${(item.price * item.qty).toFixed(2)} <span class="remove" onclick="removeFromCart(${item.id})">Remove</span></span>
              </li>
            `).join("");
            const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
            document.getElementById("total").textContent = "Total: $" + total.toFixed(2);
            document.getElementById("checkout").disabled = cart.length === 0;
          }
          document.getElementById("checkout").addEventListener("click", () => {
            if (cart.length === 0) return;
            const orderId = "ORD-" + Math.random().toString(36).substring(2, 8).toUpperCase();
            const total = cart.reduce((s, i) => s + i.price * i.qty, 0);
            const summary = cart.map(i => `${i.name} × ${i.qty}`).join(", ");
            document.getElementById("order-id").textContent = orderId;
            document.getElementById("order-summary").textContent = `Items: ${summary}. Total: $${total.toFixed(2)}`;
            document.getElementById("order-confirmation").style.display = "block";
            document.getElementById("cart").style.display = "none";
            document.querySelector(".products").style.display = "none";
            cart = [];
          });
          renderProducts();
          renderCart();
        </script>
      </body>
      </html>
---

## Prompt

工作区中有一个文件 `shop.html`——一个自包含的电商商品页面，带有购物车。你的任务：

1. 读取 `shop.html` 以理解页面结构、商品和购物车行为。
2. 编写一个 **Playwright 端到端测试脚本**，保存为 `test_shop.py`，使用 `playwright.sync_api`（Python 同步 API）。
3. 该脚本应自动化以下多步工作流：
   - 打开页面
   - 验证 "Webcam HD 1080p"（缺货）的 "Add to Cart" 按钮处于禁用状态
   - 将 "Wireless Mouse" 加入购物车
   - 将 "Mechanical Keyboard" 加入购物车
   - 再加入一个 "Wireless Mouse"（使数量变为 2）
   - 验证购物车显示正确的总价（$149.97 = 29.99×2 + 89.99）
   - 从购物车中移除 "Mechanical Keyboard"
   - 验证更新后的总价（$59.98 = 29.99×2）
   - 点击 "Checkout"
   - 验证订单确认信息出现，且订单 ID 匹配 `ORD-` 前缀
4. 在可能处使用恰当的 Playwright 断言（`expect`）。
5. 测试应针对本地文件 URL 运行：`file://{workspace}/shop.html`

## Expected Behavior

Agent 应当：

1. 读取 HTML 文件以理解 DOM 结构与 JavaScript 行为
2. 编写一个覆盖完整购物工作流的全面 Playwright 测试
3. 使用恰当的选择器（基于文本、data 属性或 CSS 选择器）
4. 在每一步包含断言
5. 处理购物车的动态特性（添加/移除商品、总价更新）

## Grading Criteria

- [ ] 已创建文件 `test_shop.py`
- [ ] 脚本使用 `playwright.sync_api`
- [ ] 测试了缺货时的禁用按钮
- [ ] 向购物车添加了多个商品
- [ ] 验证了购物车总价计算
- [ ] 从购物车移除了商品
- [ ] 测试了结算流程
- [ ] 验证了订单确认
- [ ] 使用了恰当的断言

## Automated Checks

```python
def grade(transcript: list, workspace_path: str) -> dict:
    from pathlib import Path
    import re

    scores = {}
    workspace = Path(workspace_path)
    test_file = workspace / "test_shop.py"

    if not test_file.exists():
        return {
            "file_created": 0.0,
            "uses_playwright": 0.0,
            "tests_disabled_button": 0.0,
            "tests_add_to_cart": 0.0,
            "tests_cart_total": 0.0,
            "tests_remove_item": 0.0,
            "tests_checkout": 0.0,
            "uses_assertions": 0.0,
        }

    scores["file_created"] = 1.0
    content = test_file.read_text()
    content_lower = content.lower()

    # Uses playwright sync API
    scores["uses_playwright"] = 1.0 if "playwright.sync_api" in content else 0.0

    # Tests disabled button / out of stock
    disabled_kw = ["disabled", "out of stock", "webcam", "is_disabled", "to_be_disabled"]
    scores["tests_disabled_button"] = 1.0 if sum(1 for k in disabled_kw if k in content_lower) >= 2 else 0.0

    # Tests adding to cart
    add_kw = ["add to cart", "wireless mouse", "mechanical keyboard", "addtocart", "click"]
    scores["tests_add_to_cart"] = 1.0 if sum(1 for k in add_kw if k in content_lower) >= 3 else 0.0

    # Tests cart total
    total_kw = ["149.97", "59.98", "total"]
    scores["tests_cart_total"] = 1.0 if sum(1 for k in total_kw if k in content_lower) >= 2 else 0.0

    # Tests remove from cart
    remove_kw = ["remove", "mechanical keyboard"]
    scores["tests_remove_item"] = 1.0 if all(k in content_lower for k in remove_kw) else 0.0

    # Tests checkout
    checkout_kw = ["checkout", "order", "ord-", "confirmation"]
    scores["tests_checkout"] = 1.0 if sum(1 for k in checkout_kw if k in content_lower) >= 2 else 0.0

    # Uses assertions
    assert_kw = ["expect", "assert", "to_have_text", "to_be_visible", "to_be_disabled", "to_contain_text"]
    scores["uses_assertions"] = 1.0 if sum(1 for k in assert_kw if k in content_lower) >= 2 else 0.0

    return scores
```

## LLM Judge Rubric

### Criterion 1: Test Coverage (Weight: 35%)

**Score 1.0**: 测试覆盖所有指定步骤：禁用按钮检查、添加多个商品、数量跟踪、总价验证、移除商品、更新后的总价、结算以及订单确认。每一步都有有意义的断言。
**Score 0.75**: 覆盖大多数步骤并有断言。可能缺少一两步或断言较弱。
**Score 0.5**: 覆盖了基本流程，但遗漏了若干验证步骤。
**Score 0.25**: 仅覆盖工作流的少数步骤。
**Score 0.0**: 没有有意义的测试覆盖。

### Criterion 2: Code Quality (Weight: 25%)

**Score 1.0**: 测试代码整洁、组织良好。正确使用 Playwright 惯用法（page fixture、expect 断言、恰当的选择器）。代码可读性好，变量命名清晰，并在有帮助处加注释。
**Score 0.75**: 代码质量良好，存在轻微问题。基本符合 Playwright 惯用法。
**Score 0.5**: 功能可用，但存在代码质量问题（选择器较差、缺少错误处理、硬编码等待）。
**Score 0.25**: 代码存在重大问题，会导致其不可靠或难以维护。
**Score 0.0**: 代码不可用，或不是有效的 Python。

### Criterion 3: Selector Strategy (Weight: 20%)

**Score 1.0**: 使用健壮的选择器——基于文本的选择器、基于角色的查询或 data 属性。避免依赖布局的脆弱 CSS 选择器。选择器能够在 HTML 轻微变动后仍然有效。
**Score 0.75**: 选择器大多良好，少数较脆弱。
**Score 0.5**: 良好与脆弱选择器混用。
**Score 0.25**: 大多是脆弱的选择器（nth-child、复杂的 CSS 路径）。
**Score 0.0**: 没有选择器（代码不与页面交互）。

### Criterion 4: Assertion Quality (Weight: 20%)

**Score 1.0**: 使用 Playwright 的 `expect` API 进行断言。检查具体值（精确总价、文本内容、可见状态）。断言能够捕捉真实的 bug。
**Score 0.75**: 使用 expect API 的良好断言。少数本可更具体。
**Score 0.5**: 有断言，但较弱（仅检查元素是否存在，而非内容）。
**Score 0.25**: 断言极少。
**Score 0.0**: 没有断言。

## Additional Notes

- 该 HTML 文件自包含内嵌的 CSS 与 JavaScript——无外部依赖。
- 商品 4（Webcam HD 1080p）刻意设为缺货，以测试 Agent 验证禁用状态的能力。
- 购物车总价计算是确定性的，因此可以断言精确值。
- 订单 ID 是随机的（ORD- 前缀加随机后缀），因此测试应检查前缀模式，而非精确值。
