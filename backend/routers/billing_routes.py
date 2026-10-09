"""
Razorpay billing routes for plan upgrades and payment handling.
"""
import os
import hmac
import hashlib
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from database import db
from oauth2 import verify_access_token

# Import Razorpay client
try:
    import razorpay
except ImportError:
    razorpay = None

router = APIRouter(
    prefix="/api/billing",
    tags=["Billing"]
)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Razorpay credentials from environment
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

# Validate Razorpay credentials
if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    RAZORPAY_ENABLED = False
else:
    RAZORPAY_ENABLED = True
    try:
        client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
    except Exception as e:
        print(f"[WARN] Failed to initialize Razorpay client: {e}")
        RAZORPAY_ENABLED = False

# Plan pricing configuration
PLAN_DETAILS = {
    "Free": {"amountInr": 0, "ai": 10, "storage": 5, "price": "INR 0"},
    "Pro Business": {"amountInr": 1000000, "ai": 80, "storage": 60, "price": "INR 10000"},  # 1,000,000 paise = 10,000 INR
    "Enterprise": {"amountInr": 2000000, "ai": 100, "storage": 100, "price": "INR 20000"},  # 2,000,000 paise = 20,000 INR
}

@router.post("/create-order")
async def create_order(data: dict, token: str = Depends(oauth2_scheme)):
    """
    Create a Razorpay order for plan upgrade.
    Frontend sends: {"plan": "Pro Business"}
    """
    print(f"[DEBUG] create_order called with data: {data}")
    print(f"[DEBUG] RAZORPAY_ENABLED: {RAZORPAY_ENABLED}")

    if not RAZORPAY_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Razorpay credentials are not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in backend .env, then restart backend."
        )

    plan_name = data.get("plan", "").strip()
    print(f"[DEBUG] Plan requested: {plan_name}")
    print(f"[DEBUG] Available plans: {list(PLAN_DETAILS.keys())}")

    if plan_name not in PLAN_DETAILS:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan_name}")

    plan_info = PLAN_DETAILS[plan_name]
    amount = plan_info["amountInr"]

    print(f"[DEBUG] Plan info: {plan_info}")
    print(f"[DEBUG] Amount in paise: {amount}")

    # For free plan, no payment needed
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Cannot create payment order for Free plan")

    try:
        order_data = {
            "amount": amount,  # Amount in paise
            "currency": "INR",
            "payment_capture": 1,  # Auto-capture payment
            "receipt": f"plan_{plan_name}_{int(__import__('time').time())}",
        }

        print(f"[DEBUG] Creating Razorpay order with data: {order_data}")
        order = client.order.create(data=order_data)
        print(f"[DEBUG] Order created successfully: {order}")

        return {
            "key_id": RAZORPAY_KEY_ID,
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
            "message": f"Order created for {plan_name} plan"
        }

    except Exception as e:
        print(f"[ERROR] Failed to create Razorpay order: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Razorpay order: {str(e)}"
        )

@router.post("/verify")
async def verify_payment(data: dict, token: str = Depends(oauth2_scheme)):
    """
    Verify Razorpay payment and upgrade user plan.
    Frontend sends:
    {
        "plan": "Pro",
        "razorpay_order_id": "...",
        "razorpay_payment_id": "...",
        "razorpay_signature": "..."
    }
    """
    if not RAZORPAY_ENABLED:
        raise HTTPException(
            status_code=400,
            detail="Razorpay credentials are not configured"
        )

    try:
        # Extract payment details from frontend
        order_id = data.get("razorpay_order_id")
        payment_id = data.get("razorpay_payment_id")
        signature = data.get("razorpay_signature")
        plan_name = data.get("plan", "").strip()

        if not all([order_id, payment_id, signature, plan_name]):
            raise HTTPException(status_code=400, detail="Missing required payment fields")

        if plan_name not in PLAN_DETAILS:
            raise HTTPException(status_code=400, detail=f"Invalid plan: {plan_name}")

        # Verify signature to ensure payment authenticity
        message = f"{order_id}|{payment_id}"
        calculated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()

        if calculated_signature != signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")

        # Signature is valid - update user plan in MongoDB
        # Note: In production, you might want to verify payment status with Razorpay API
        # For now, we trust the signature verification

        plan_info = PLAN_DETAILS[plan_name]

        # Get user from token
        payload = verify_access_token(token)
        user_id = payload.get("user_id")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get current user settings to check for downgrade attempts
        current_settings = db["settings"].find_one({"user_id": user_id})
        current_plan = current_settings.get("plan", "Free") if current_settings else "Free"
        payment_status = current_settings.get("payment_status", "none") if current_settings else "none"

        # Prevent downgrades: users with active paid plans can only upgrade or stay same
        # Define plan tier order
        plan_tiers = {"Free": 0, "Pro Business": 1, "Enterprise": 2}
        current_tier = plan_tiers.get(current_plan, 0)
        new_tier = plan_tiers.get(plan_name, 0)

        # Check if user has active subscription and is trying to downgrade
        if payment_status == "active" and current_plan != "Free":
            if new_tier < current_tier:
                raise HTTPException(
                    status_code=403,
                    detail=f"Cannot downgrade from {current_plan} to {plan_name}. Users with active subscriptions can only upgrade or maintain their current plan."
                )

        # Update user settings in MongoDB
        updated_settings = {
            "user_id": user_id,
            "plan": plan_name,
            "price": plan_info["price"],
            "cardLast4": payment_id[-4:] if len(payment_id) >= 4 else "",
            "cardExpiry": "",  # Razorpay doesn't return this
            "usage": {
                "ai": plan_info["ai"],
                "storage": plan_info["storage"]
            },
            "paymentId": payment_id,
            "orderId": order_id,
            "payment_status": "active"
        }

        # Calculate plan expiry (1 year from now)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        plan_expiry = now + timedelta(days=365)

        updated_settings["plan_purchased_date"] = now.isoformat()
        updated_settings["plan_expiry_date"] = plan_expiry.isoformat()
        updated_settings["remaining_days"] = 365

        db["settings"].update_one(
            {"user_id": user_id},
            {"$set": updated_settings},
            upsert=True
        )

        print(f"[OK] Plan {plan_name} activated for user {user_id} until {plan_expiry.strftime('%Y-%m-%d')}")

        return {
            "message": f"Payment successful. {plan_name} plan activated for 1 year!",
            "settings": updated_settings,
            "status": "success",
            "plan_expiry": plan_expiry.isoformat(),
            "remaining_days": 365
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Payment verification failed: {str(e)}"
        )

@router.get("/subscription-status")
async def get_subscription_status(token: str = Depends(oauth2_scheme)):
    """
    Get current subscription status with expiry info and remaining days.
    Returns payment_status, expired/active, remaining days, etc.
    """
    from datetime import datetime

    payload = verify_access_token(token)
    user_id = payload.get("user_id")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    # Get user settings from MongoDB
    settings = db["settings"].find_one({"user_id": user_id})

    if not settings:
        return {
            "plan": "Free",
            "payment_status": "none",
            "is_expired": False,
            "remaining_days": 0,
            "plan_expiry_date": None,
            "message": "User is on Free plan"
        }

    # Check if plan is expired
    plan_expiry_str = settings.get("plan_expiry_date")
    payment_status = settings.get("payment_status", "none")
    plan_name = settings.get("plan", "Free")

    if plan_expiry_str:
        plan_expiry = datetime.fromisoformat(plan_expiry_str)
        now = datetime.utcnow()
        remaining = (plan_expiry - now).days
        is_expired = remaining <= 0

        # If expired, revert to Free plan
        if is_expired and plan_name != "Free":
            db["settings"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "plan": "Free",
                        "payment_status": "expired",
                        "remaining_days": 0,
                        "usage": {"ai": 5, "storage": 1}
                    }
                }
            )
            return {
                "plan": "Free",
                "payment_status": "expired",
                "is_expired": True,
                "remaining_days": 0,
                "plan_expiry_date": plan_expiry_str,
                "message": f"Your {plan_name} plan has expired. You are now on Free plan."
            }

        return {
            "plan": plan_name,
            "payment_status": payment_status,
            "is_expired": is_expired,
            "remaining_days": max(remaining, 0),
            "plan_expiry_date": plan_expiry_str,
            "plan_purchased_date": settings.get("plan_purchased_date"),
            "message": f"{plan_name} plan active for {max(remaining, 0)} more days"
        }

    return {
        "plan": plan_name,
        "payment_status": payment_status,
        "is_expired": False,
        "remaining_days": 0,
        "plan_expiry_date": None,
        "message": f"User is on {plan_name} plan"
    }

@router.get("/health")
async def billing_health():
    """Check if Razorpay is configured and operational."""
    return {
        "status": "healthy" if RAZORPAY_ENABLED else "not_configured",
        "razorpay_configured": RAZORPAY_ENABLED,
        "message": "Razorpay is ready" if RAZORPAY_ENABLED else "Razorpay credentials missing"
    }
