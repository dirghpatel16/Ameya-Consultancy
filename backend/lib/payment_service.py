from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger("ameya.payment")

RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "rzp_test_TY2oVdGaLLmUYy")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "g8SXpqXOMQLrWglVmdwtXz4u")
CONSULTATION_FEE_INR = int(os.environ.get("CONSULTATION_FEE_INR", "1000"))

RAZORPAY_ORDERS_URL = "https://api.razorpay.com/v1/orders"


def _get_ssl_context():
    try:
        return ssl.create_default_context()
    except Exception:
        return ssl._create_unverified_context()


def create_razorpay_order(
    amount_inr: int = CONSULTATION_FEE_INR,
    receipt: str = "AMY-ORDER",
    notes: dict | None = None,
) -> dict:
    """
    Creates a Razorpay Order for upfront payment.
    Amount is converted to paise (₹1,000 = 100,000 paise).
    """
    key_id = os.environ.get("RAZORPAY_KEY_ID", RAZORPAY_KEY_ID)
    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", RAZORPAY_KEY_SECRET)
    amount_paise = amount_inr * 100

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt[:40],
        "notes": notes or {},
        "payment_capture": 1,
    }

    auth_str = f"{key_id}:{key_secret}"
    auth_header = "Basic " + base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")

    req = urllib.request.Request(
        RAZORPAY_ORDERS_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": auth_header,
            "Content-Type": "application/json",
            "User-Agent": "AmeyaConsultancy/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=12, context=ssl.create_default_context()) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return {
                "order_id": body.get("id"),
                "amount": body.get("amount", amount_paise),
                "amount_inr": amount_inr,
                "currency": body.get("currency", "INR"),
                "key_id": key_id,
            }
    except urllib.error.URLError:
        try:
            with urllib.request.urlopen(req, timeout=12, context=ssl._create_unverified_context()) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return {
                    "order_id": body.get("id"),
                    "amount": body.get("amount", amount_paise),
                    "amount_inr": amount_inr,
                    "currency": body.get("currency", "INR"),
                    "key_id": key_id,
                }
        except Exception as fallback_exc:
            logger.error("Razorpay order creation fallback failed: %s", fallback_exc)
            raise RuntimeError("Payment gateway currently unavailable. Please try again or WhatsApp Dr. Nisha.") from fallback_exc
    except urllib.error.HTTPError as http_err:
        err_body = http_err.read().decode("utf-8", errors="ignore")
        logger.error("Razorpay order creation HTTP error %s: %s", http_err.code, err_body)
        raise RuntimeError(f"Razorpay order failed: {http_err.code}") from http_err
    except Exception as exc:
        logger.error("Failed to connect to Razorpay: %s", exc)
        raise RuntimeError("Payment gateway currently unavailable. Please try again or WhatsApp Dr. Nisha.") from exc


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """
    Verifies Razorpay HMAC SHA256 signature for payment authenticity.
    """
    if not (order_id and payment_id and signature):
        return False

    key_secret = os.environ.get("RAZORPAY_KEY_SECRET", RAZORPAY_KEY_SECRET)
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected_signature = hmac.new(
        key_secret.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()

    is_valid = hmac.compare_digest(expected_signature, signature)
    if not is_valid:
        logger.warning(
            "Razorpay signature mismatch for order %s and payment %s",
            order_id,
            payment_id,
        )
    return is_valid
