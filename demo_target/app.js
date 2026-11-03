// Acme Admin - Demo Target Application
// Purpose: ScreenGuard watches this app. The app DOES NOT block mistakes; it records them in window.__state.truth.

const ORDERS = [
  { id: "ORD-1001", customer: "Acme Corp", items: "Office Desk, Ergo Chair", total: 180.00 },
  { id: "ORD-1002", customer: "Globex Logistics", items: "Heavy Duty Scanner, Label Printer", total: 240.00 },
  { id: "ORD-1003", customer: "Soylent Industries", items: "10x Reusable Packaging Totes", total: 95.00 },
  { id: "ORD-1004", customer: "Initech Consulting", items: "Laser Projector, HDMI Cables", total: 320.00 },
  { id: "ORD-1005", customer: "Umbrella Bio", items: "Safety Goggles, Lab Stools", total: 150.00 },
];

window.__state = {
  screen: "login",
  selectedOrder: null,
  refundDraft: {
    reason: "",
    amount: "",
    managerApproved: false,
    note: ""
  },
  refundResult: null,
  actions: [],
  truth: {
    steps_done: [],
    current_step: 1,
    violations: []
  }
};

function logAction(type, target, value) {
  const action = { ts: Date.now() / 1000, type, target, value };
  window.__state.actions.push(action);
  return action;
}

function markStepDone(stepNum) {
  if (!window.__state.truth.steps_done.includes(stepNum)) {
    window.__state.truth.steps_done.push(stepNum);
    window.__state.truth.current_step = stepNum + 1;
  }
}

function recordViolation(type, step, details) {
  window.__state.truth.violations.push({
    type,
    step,
    ts: Date.now() / 1000,
    details
  });
}

function render() {
  const root = document.getElementById("app-root");
  const userStatus = document.getElementById("user-status");

  if (window.__state.screen === "login") {
    userStatus.textContent = "Not logged in";
    root.innerHTML = `
      <div class="card" style="max-width: 520px; margin: 40px auto;">
        <h2>Sign In to Acme Admin</h2>
        <div class="demo-credentials">
          <strong>Demo Credentials:</strong><br>
          Username: <code>demo@acme.com</code><br>
          Password: <code>demo123</code>
        </div>
        <form id="form-login">
          <div class="form-group">
            <label for="inp-username">Username</label>
            <input type="text" id="inp-username" data-testid="inp-username" value="demo@acme.com" autocomplete="off" />
          </div>
          <div class="form-group">
            <label for="inp-password">Password</label>
            <input type="password" id="inp-password" data-testid="inp-password" value="demo123" />
          </div>
          <button type="submit" id="btn-signin" data-testid="btn-signin" class="btn btn-primary" style="width: 100%;">Sign in</button>
        </form>
      </div>
    `;

    document.getElementById("form-login").addEventListener("submit", (e) => {
      e.preventDefault();
      const u = document.getElementById("inp-username").value;
      const p = document.getElementById("inp-password").value;
      logAction("click", "btn-signin", { username: u });

      if (u === "demo@acme.com" && p === "demo123") {
        markStepDone(1);
      } else {
        recordViolation("wrong_value", 1, `Invalid login credentials: ${u}`);
      }

      window.__state.screen = "orders";
      render();
    });
    return;
  }

  userStatus.textContent = "Logged in: demo@acme.com";

  if (window.__state.screen === "orders") {
    root.innerHTML = `
      <div class="card">
        <h2>Orders Overview</h2>
        <p style="color: var(--text-muted); font-size: 19px;">Select an order to view details or initiate refunds.</p>
        <table>
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Customer</th>
              <th>Total ($)</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            ${ORDERS.map(o => `
              <tr>
                <td><strong>${o.id}</strong></td>
                <td>${o.customer}</td>
                <td>$${o.total.toFixed(2)}</td>
                <td>
                  <button class="btn btn-secondary btn-open-order" data-order-id="${o.id}" id="btn-open-${o.id.toLowerCase()}" data-testid="btn-open-${o.id.toLowerCase()}">
                    Open
                  </button>
                </td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;

    document.querySelectorAll(".btn-open-order").forEach(btn => {
      btn.addEventListener("click", () => {
        const orderId = btn.getAttribute("data-order-id");
        logAction("click", btn.id, { orderId });

        const ord = ORDERS.find(o => o.id === orderId);
        window.__state.selectedOrder = ord;

        if (orderId === "ORD-1002") {
          markStepDone(2);
        } else {
          recordViolation("wrong_value", 2, `Opened order ${orderId} instead of ORD-1002`);
        }

        window.__state.screen = "order_detail";
        render();
      });
    });
    return;
  }

  if (window.__state.screen === "order_detail") {
    const o = window.__state.selectedOrder || ORDERS[1];
    markStepDone(3); // Checked order total

    root.innerHTML = `
      <div class="card" style="max-width: 800px; margin: 0 auto;">
        <h2>Order Detail: ${o.id}</h2>
        <div class="detail-row">
          <span class="detail-label">Customer:</span>
          <span class="detail-value">${o.customer}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Purchased Items:</span>
          <span class="detail-value">${o.items}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Order Total:</span>
          <span class="detail-value" style="font-size: 24px; color: #1e40af;">$${o.total.toFixed(2)}</span>
        </div>
        <div class="btn-group">
          <button id="btn-start-refund" data-testid="btn-start-refund" class="btn btn-primary">Start refund</button>
          <button id="btn-back-orders" data-testid="btn-back-orders" class="btn btn-secondary">Back</button>
        </div>
      </div>
    `;

    document.getElementById("btn-start-refund").addEventListener("click", () => {
      logAction("click", "btn-start-refund", null);
      markStepDone(4);
      window.__state.screen = "refund_form";
      render();
    });

    document.getElementById("btn-back-orders").addEventListener("click", () => {
      window.__state.screen = "orders";
      render();
    });
    return;
  }

  if (window.__state.screen === "refund_form") {
    const o = window.__state.selectedOrder || ORDERS[1];
    const draft = window.__state.refundDraft;

    root.innerHTML = `
      <div class="card" style="max-width: 760px; margin: 0 auto;">
        <h2>Process Customer Refund (${o.id})</h2>
        <p style="color: var(--text-muted); font-size: 19px;">Order Total: <strong>$${o.total.toFixed(2)}</strong></p>
        <form id="form-refund">
          <div class="form-group">
            <label for="sel-reason">Refund Reason</label>
            <select id="sel-reason" data-testid="sel-reason">
              <option value="">-- Choose reason --</option>
              <option value="Damaged item" ${draft.reason === "Damaged item" ? "selected" : ""}>Damaged item</option>
              <option value="Wrong item" ${draft.reason === "Wrong item" ? "selected" : ""}>Wrong item</option>
              <option value="Customer changed mind" ${draft.reason === "Customer changed mind" ? "selected" : ""}>Customer changed mind</option>
            </select>
          </div>

          <div class="form-group">
            <label for="inp-amount">Refund Amount ($)</label>
            <input type="number" step="0.01" id="inp-amount" data-testid="inp-amount" placeholder="0.00" value="${draft.amount || ""}" />
          </div>

          <div class="checkbox-group">
            <input type="checkbox" id="chk-manager" data-testid="chk-manager" ${draft.managerApproved ? "checked" : ""} />
            <label for="chk-manager">Manager approved (required over $100)</label>
          </div>

          <div class="form-group">
            <label for="txt-note">Internal Notes</label>
            <textarea id="txt-note" data-testid="txt-note" rows="3" placeholder="Optional notes...">${draft.note || ""}</textarea>
          </div>

          <div class="btn-group">
            <button type="button" id="btn-review" data-testid="btn-review" class="btn btn-primary">Review refund</button>
            <button type="button" id="btn-cancel" data-testid="btn-cancel" class="btn btn-danger">Cancel</button>
          </div>
        </form>
      </div>
    `;

    document.getElementById("btn-review").addEventListener("click", () => {
      const reason = document.getElementById("sel-reason").value;
      const amountStr = document.getElementById("inp-amount").value;
      const managerApproved = document.getElementById("chk-manager").checked;
      const note = document.getElementById("txt-note").value;

      window.__state.refundDraft = { reason, amount: amountStr, managerApproved, note };
      logAction("click", "btn-review", { reason, amount: amountStr, managerApproved });

      const amountVal = parseFloat(amountStr) || 0;

      // Evaluation Ground Truth Validation
      if (!reason) {
        recordViolation("wrong_order", 8, "Clicked Review refund before selecting a reason.");
      } else if (reason === "Damaged item") {
        markStepDone(5);
      } else {
        recordViolation("wrong_control", 5, `Selected reason '${reason}' instead of 'Damaged item'.`);
      }

      if (amountStr === "120.00" || amountVal === 120) {
        markStepDone(6);
      } else {
        recordViolation("wrong_value", 6, `Entered amount '${amountStr}' instead of expected '120.00'.`);
      }

      if (amountVal > 100) {
        if (managerApproved) {
          markStepDone(7);
        } else {
          recordViolation("skipped_step", 7, "Skipped manager approval on refund over $100.");
        }
      }

      markStepDone(8); // Clicked Review refund
      window.__state.screen = "review";
      render();
    });

    document.getElementById("btn-cancel").addEventListener("click", () => {
      logAction("click", "btn-cancel", null);
      window.__state.screen = "order_detail";
      render();
    });
    return;
  }

  if (window.__state.screen === "review") {
    const o = window.__state.selectedOrder || ORDERS[1];
    const draft = window.__state.refundDraft;
    markStepDone(9); // Review details displayed

    root.innerHTML = `
      <div class="card" style="max-width: 760px; margin: 0 auto;">
        <h2>Review Refund Authorization</h2>
        <div class="detail-row">
          <span class="detail-label">Order ID:</span>
          <span class="detail-value">${o.id}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Reason:</span>
          <span class="detail-value">${draft.reason || "(None specified)"}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Refund Amount:</span>
          <span class="detail-value" style="font-size: 24px; color: #1e40af;">$${parseFloat(draft.amount || 0).toFixed(2)}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">Manager Approved:</span>
          <span class="detail-value" style="color: ${draft.managerApproved ? '#15803d' : '#b91c1c'}; font-weight: 800;">
            ${draft.managerApproved ? "YES" : "NO"}
          </span>
        </div>
        ${draft.note ? `
        <div class="detail-row">
          <span class="detail-label">Note:</span>
          <span class="detail-value">${draft.note}</span>
        </div>` : ""}

        <div class="btn-group">
          <button id="btn-confirm" data-testid="btn-confirm" class="btn btn-primary">Confirm refund</button>
          <button id="btn-back-form" data-testid="btn-back-form" class="btn btn-secondary">Back</button>
        </div>
      </div>
    `;

    document.getElementById("btn-confirm").addEventListener("click", () => {
      const amountVal = parseFloat(draft.amount || 0);
      logAction("click", "btn-confirm", { amount: amountVal, managerApproved: draft.managerApproved });

      if (amountVal > 100 && !draft.managerApproved) {
        recordViolation("premature_submit", 10, "Submitted refund over $100 without manager approval.");
      }

      markStepDone(10);
      window.__state.refundResult = {
        refId: "REF-" + Math.floor(1000 + Math.random() * 9000),
        amount: amountVal
      };
      window.__state.screen = "success";
      render();
    });

    document.getElementById("btn-back-form").addEventListener("click", () => {
      window.__state.screen = "refund_form";
      render();
    });
    return;
  }

  if (window.__state.screen === "success") {
    const res = window.__state.refundResult || { refId: "REF-4821", amount: 120.00 };
    root.innerHTML = `
      <div class="card" style="max-width: 680px; margin: 40px auto; text-align: center;">
        <div class="alert-success">
          Refund issued successfully!
        </div>
        <h2>Transaction Confirmation</h2>
        <p style="font-size: 22px;">Refund Reference: <strong id="lbl-ref" data-testid="lbl-ref" style="color: #1e40af;">${res.refId}</strong></p>
        <p style="font-size: 20px;">Amount refunded: <strong>$${res.amount.toFixed(2)}</strong></p>
        <div class="btn-group" style="justify-content: center;">
          <button id="btn-done" data-testid="btn-done" class="btn btn-primary">Back to Orders</button>
        </div>
      </div>
    `;

    document.getElementById("btn-done").addEventListener("click", () => {
      window.__state.screen = "orders";
      render();
    });
    return;
  }
}

// Initial mount
render();
