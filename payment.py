"""
payment.py
----------
Shop payment methods module.
Supports: Credit/Debit Card, PayPal, Cash, Bank Transfer, Crypto.
"""

import uuid
from datetime import datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────────────

class PaymentMethod(Enum):
    CARD          = "card"
    PAYPAL        = "paypal"
    CASH          = "cash"
    BANK_TRANSFER = "bank_transfer"
    CRYPTO        = "crypto"


class PaymentStatus(Enum):
    SUCCESS  = "success"
    FAILED   = "failed"
    PENDING  = "pending"
    REFUNDED = "refunded"


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _generate_transaction_id():
    """Generates a unique transaction ID."""
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"


def _generate_order_id():
    """Generates a unique order ID."""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


def _format_currency(amount: float) -> str:
    """Formats a float as a currency string."""
    return f"${amount:,.2f}"


def _build_receipt(order_id, txn_id, method, amount, status, change=0.0, meta=None):
    """Builds a standardized receipt dictionary."""
    return {
        "order_id":       order_id,
        "transaction_id": txn_id,
        "method":         method.value,
        "amount":         round(amount, 2),
        "change":         round(change, 2),
        "status":         status.value,
        "timestamp":      datetime.utcnow().isoformat() + "Z",
        "meta":           meta or {},
    }


# ─── Payment Methods ──────────────────────────────────────────────────────────

def pay_by_card(amount: float, card_number: str, expiry: str, cvv: str, cardholder: str) -> dict:
    """
    Processes a credit/debit card payment.

    Args:
        amount      (float): Total amount to charge.
        card_number (str):   16-digit card number (digits only).
        expiry      (str):   Expiry date in MM/YY format.
        cvv         (str):   3 or 4 digit CVV.
        cardholder  (str):   Full name on card.

    Returns:
        dict: Payment receipt.

    Example:
        pay_by_card(99.99, "4111111111111111", "12/26", "123", "John Doe")
    """
    # Validate inputs
    card_digits = card_number.replace(" ", "").replace("-", "")
    if len(card_digits) != 16 or not card_digits.isdigit():
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CARD, amount, PaymentStatus.FAILED,
            meta={"error": "Invalid card number. Must be 16 digits."}
        )

    if len(cvv) not in (3, 4) or not cvv.isdigit():
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CARD, amount, PaymentStatus.FAILED,
            meta={"error": "Invalid CVV."}
        )

    if amount <= 0:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CARD, amount, PaymentStatus.FAILED,
            meta={"error": "Amount must be greater than zero."}
        )

    order_id = _generate_order_id()
    txn_id   = _generate_transaction_id()

    print(f"\n💳 Card Payment")
    print(f"   Cardholder : {cardholder}")
    print(f"   Card       : **** **** **** {card_digits[-4:]}")
    print(f"   Amount     : {_format_currency(amount)}")
    print(f"   Status     : SUCCESS ✅")

    return _build_receipt(
        order_id, txn_id, PaymentMethod.CARD, amount, PaymentStatus.SUCCESS,
        meta={"cardholder": cardholder, "last4": card_digits[-4:], "expiry": expiry}
    )


def pay_by_paypal(amount: float, email: str) -> dict:
    """
    Processes a PayPal payment.

    Args:
        amount (float): Total amount to charge.
        email  (str):   PayPal account email.

    Returns:
        dict: Payment receipt.

    Example:
        pay_by_paypal(49.99, "user@example.com")
    """
    if "@" not in email or "." not in email.split("@")[-1]:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.PAYPAL, amount, PaymentStatus.FAILED,
            meta={"error": "Invalid PayPal email address."}
        )

    if amount <= 0:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.PAYPAL, amount, PaymentStatus.FAILED,
            meta={"error": "Amount must be greater than zero."}
        )

    order_id = _generate_order_id()
    txn_id   = _generate_transaction_id()

    print(f"\n🅿️  PayPal Payment")
    print(f"   Account : {email}")
    print(f"   Amount  : {_format_currency(amount)}")
    print(f"   Status  : SUCCESS ✅")

    return _build_receipt(
        order_id, txn_id, PaymentMethod.PAYPAL, amount, PaymentStatus.SUCCESS,
        meta={"paypal_email": email}
    )


def pay_by_cash(amount: float, amount_tendered: float) -> dict:
    """
    Processes a cash payment and calculates change.

    Args:
        amount          (float): Total amount due.
        amount_tendered (float): Cash given by the customer.

    Returns:
        dict: Payment receipt with change.

    Example:
        pay_by_cash(37.50, 50.00)
    """
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    if amount_tendered < amount:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CASH, amount, PaymentStatus.FAILED,
            meta={
                "error": f"Insufficient cash. Need {_format_currency(amount)}, "
                         f"received {_format_currency(amount_tendered)}."
            }
        )

    change   = round(amount_tendered - amount, 2)
    order_id = _generate_order_id()
    txn_id   = _generate_transaction_id()

    print(f"\n💵 Cash Payment")
    print(f"   Amount Due : {_format_currency(amount)}")
    print(f"   Tendered   : {_format_currency(amount_tendered)}")
    print(f"   Change     : {_format_currency(change)}")
    print(f"   Status     : SUCCESS ✅")

    return _build_receipt(
        order_id, txn_id, PaymentMethod.CASH, amount, PaymentStatus.SUCCESS,
        change=change,
        meta={"amount_tendered": amount_tendered}
    )


def pay_by_bank_transfer(amount: float, account_name: str, account_number: str, routing_number: str) -> dict:
    """
    Processes a bank transfer payment.

    Args:
        amount         (float): Total amount to transfer.
        account_name   (str):   Account holder's name.
        account_number (str):   Bank account number.
        routing_number (str):   Bank routing number (9 digits).

    Returns:
        dict: Payment receipt (status: pending until confirmed).

    Example:
        pay_by_bank_transfer(500.00, "Jane Smith", "123456789", "021000021")
    """
    if len(routing_number) != 9 or not routing_number.isdigit():
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.BANK_TRANSFER, amount, PaymentStatus.FAILED,
            meta={"error": "Routing number must be exactly 9 digits."}
        )

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    order_id = _generate_order_id()
    txn_id   = _generate_transaction_id()

    print(f"\n🏦 Bank Transfer")
    print(f"   Account    : {account_name}")
    print(f"   Acc No     : ***{account_number[-4:]}")
    print(f"   Amount     : {_format_currency(amount)}")
    print(f"   Status     : PENDING ⏳ (awaiting bank confirmation)")

    return _build_receipt(
        order_id, txn_id, PaymentMethod.BANK_TRANSFER, amount, PaymentStatus.PENDING,
        meta={
            "account_name":   account_name,
            "account_last4":  account_number[-4:],
            "routing_number": routing_number,
        }
    )


def pay_by_crypto(amount: float, wallet_address: str, currency: str = "BTC") -> dict:
    """
    Processes a cryptocurrency payment.

    Args:
        amount         (float): Total amount in USD equivalent.
        wallet_address (str):   Destination crypto wallet address.
        currency       (str):   Crypto currency symbol (BTC, ETH, USDT).

    Returns:
        dict: Payment receipt.

    Example:
        pay_by_crypto(200.00, "1A2b3C4d5E6f7G8h9I0j", "ETH")
    """
    SUPPORTED = ["BTC", "ETH", "USDT", "BNB", "SOL"]

    if currency.upper() not in SUPPORTED:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CRYPTO, amount, PaymentStatus.FAILED,
            meta={"error": f"Unsupported crypto. Supported: {', '.join(SUPPORTED)}"}
        )

    if len(wallet_address) < 20:
        return _build_receipt(
            _generate_order_id(), _generate_transaction_id(),
            PaymentMethod.CRYPTO, amount, PaymentStatus.FAILED,
            meta={"error": "Invalid wallet address."}
        )

    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")

    order_id = _generate_order_id()
    txn_id   = _generate_transaction_id()

    print(f"\n🪙 Crypto Payment ({currency.upper()})")
    print(f"   Wallet  : {wallet_address[:6]}...{wallet_address[-4:]}")
    print(f"   Amount  : {_format_currency(amount)} (USD equiv.)")
    print(f"   Status  : PENDING ⏳ (awaiting blockchain confirmation)")

    return _build_receipt(
        order_id, txn_id, PaymentMethod.CRYPTO, amount, PaymentStatus.PENDING,
        meta={
            "currency":       currency.upper(),
            "wallet_address": wallet_address,
        }
    )


# ─── Refund ───────────────────────────────────────────────────────────────────

def process_refund(original_receipt: dict, reason: str = "Customer request") -> dict:
    """
    Processes a refund for a completed payment.

    Args:
        original_receipt (dict): The receipt from the original payment.
        reason           (str):  Reason for refund.

    Returns:
        dict: Refund receipt.

    Example:
        process_refund(receipt, reason="Item out of stock")
    """
    if original_receipt.get("status") != PaymentStatus.SUCCESS.value:
        raise ValueError("Only successful payments can be refunded.")

    refund_txn = _generate_transaction_id()

    print(f"\n↩️  Refund Processed")
    print(f"   Original TXN : {original_receipt['transaction_id']}")
    print(f"   Refund TXN   : {refund_txn}")
    print(f"   Amount       : {_format_currency(original_receipt['amount'])}")
    print(f"   Reason       : {reason}")
    print(f"   Status       : REFUNDED ✅")

    return {
        "refund_transaction_id":    refund_txn,
        "original_transaction_id":  original_receipt["transaction_id"],
        "original_order_id":        original_receipt["order_id"],
        "method":                   original_receipt["method"],
        "amount_refunded":          original_receipt["amount"],
        "reason":                   reason,
        "status":                   PaymentStatus.REFUNDED.value,
        "timestamp":                datetime.utcnow().isoformat() + "Z",
    }


# ─── Quick Demo ───────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # Card payment
    r1 = pay_by_card(99.99, "4111111111111111", "12/26", "123", "John Doe")
    print(r1)

    # PayPal
    r2 = pay_by_paypal(49.99, "john@example.com")
    print(r2)

    # Cash with change
    r3 = pay_by_cash(37.50, 50.00)
    print(r3)

    # Bank transfer
    r4 = pay_by_bank_transfer(500.00, "Jane Smith", "987654321", "021000021")
    print(r4)

    # Crypto
    r5 = pay_by_crypto(200.00, "1A2b3C4d5E6f7G8h9I0jK1L2M", "ETH")
    print(r5)

    # Refund
    refund = process_refund(r1, reason="Wrong item shipped")
    print(refund)
