from enum import Enum


class PlanType(str, Enum):
    FREE = "free"
    PRO = "pro"


# Central place for all plan rules — add new plans here later
PLAN_LIMITS = {
    PlanType.FREE: {
        "name": "Free",
        "requests_per_day": 5,
        "price": 0,
        "description": "Great for trying things out"
    },
    PlanType.PRO: {
        "name": "Pro",
        "requests_per_day": 100,
        "price": 19,
        "description": "For developers who debug daily"
    }
}


def get_plan_limit(plan: str) -> int:
    """Returns how many requests/day a plan allows."""
    plan_data = PLAN_LIMITS.get(plan)
    if not plan_data:
        raise ValueError(f"Unknown plan: {plan}")
    return plan_data["requests_per_day"]