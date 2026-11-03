# Error Catalog: Acme Admin Refund Flow

This document defines the 5 error types and concrete examples for the Acme Admin refund procedure (10 steps).
These errors are intentionally allowed by the demo target application without blocking the user, so that ScreenGuard's observation and step engine can detect and warn about them.

The application automatically records user actions and tracks ground truth in `window.__state.truth.violations`.

---

## 1. Skipped Step (`skipped_step`)
- **Definition**: The user bypasses an essential step and moves ahead to a subsequent action without performing the required step.
- **Example in Refund Flow**:
  - The refund amount entered is **$120.00** (which is over $100.00). Step 7 requires: *"Tick Manager approved (required over $100)"*.
  - The user leaves the checkbox unticked and directly clicks **Review refund** (Step 8).
- **Recorded in `truth.violations`**:
  ```json
  {
    "type": "skipped_step",
    "step": 7,
    "ts": 1793683000.123,
    "details": "Manager approval required for amounts over $100 was skipped before review."
  }
  ```

---

## 2. Wrong Order (`wrong_order`)
- **Definition**: Actions are performed out of sequence relative to the standard operating procedure dependencies.
- **Example in Refund Flow**:
  - On the Refund Form, the user clicks **Review refund** (Step 8) before selecting a reason from the dropdown (Step 5) or entering the amount (Step 6).
- **Recorded in `truth.violations`**:
  ```json
  {
    "type": "wrong_order",
    "step": 8,
    "ts": 1793683005.456,
    "details": "Clicked Review refund before specifying a refund reason and amount."
  }
  ```

---

## 3. Wrong Value (`wrong_value`)
- **Definition**: The user fills in an input field with an incorrect value that contradicts the procedure instructions.
- **Example in Refund Flow**:
  - The procedure specifies entering **120.00**. The user enters **1200.00** (exceeding the order total) or **50.00**.
  - Alternatively, on the Orders page, the user opens **ORD-1003** instead of **ORD-1002**.
- **Recorded in `truth.violations`**:
  ```json
  {
    "type": "wrong_value",
    "step": 6,
    "ts": 1793683010.789,
    "details": "Entered amount '1200.00' instead of expected '120.00'."
  }
  ```

---

## 4. Wrong Control (`wrong_control`)
- **Definition**: The user interacts with the wrong option, tab, or button among multiple choices.
- **Example in Refund Flow**:
  - In the Reason dropdown, the procedure specifies **Damaged item**.
  - The user selects **Wrong item** or **Customer changed mind**.
- **Recorded in `truth.violations`**:
  ```json
  {
    "type": "wrong_control",
    "step": 5,
    "ts": 1793683015.012,
    "details": "Selected reason 'Wrong item' instead of 'Damaged item'."
  }
  ```

---

## 5. Premature Submit (`premature_submit`)
- **Definition**: The user executes a final submission or confirmation action before prerequisites or approvals are satisfied.
- **Example in Refund Flow**:
  - On the Review screen, the manager approval is marked as **No** (not approved) for a **$120.00** refund, but the user clicks **Confirm refund** anyway.
- **Recorded in `truth.violations`**:
  ```json
  {
    "type": "premature_submit",
    "step": 10,
    "ts": 1793683020.345,
    "details": "Clicked Confirm refund with unapproved high-risk transaction."
  }
  ```
