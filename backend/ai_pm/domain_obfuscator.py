"""Domain obfuscation — mask industry intent while preserving structural challenge shape."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..privacy_proxy.models import SanitizedMetadata
from .models import SensitivityTag

_FOOD_MERCHANT_TOKENS = frozenset(
    {
        "merchant",
        "checkout",
        "cart",
        "dine",
        "restaurant",
        "food",
        "voucher",
        "delivery",
        "grab",
        "eats",
    }
)

_RIDE_TOKENS = frozenset({"dispatch", "driver", "ride", "fleet", "geo", "hailing"})

_FINTECH_TOKENS = frozenset({"payment", "billing", "transaction", "retry", "invoice", "subscription"})


@dataclass
class DomainTransform:
    domain_proxy: str
    public_title: str
    public_narrative: str
    internal_intent: str
    transform_rationale: str
    brand_proxy: str
    field_map: dict[str, str]


# Explicit column renames per domain (original → public domain-equivalent)
_FOOD_TO_EQUIPMENT_FIELDS: dict[str, str] = {
    "voucher_code": "rental_credit_code",
    "restaurant_id": "locker_id",
    "dine_in_session": "reservation_session",
    "merchant_id": "locker_id",
    "discovery_query": "inventory_query",
    "checkout_step": "redeem_step",
    "feature_request": "capability_request",
    "screen_name": "view_name",
    "ux_friction": "interaction_friction",
    "cart_abandon": "cart_abandon_flag",
    "map_pin_lat": "geo_lat",
    "map_pin_lng": "geo_lng",
}

_FOOD_TO_EQUIPMENT_SUBSTRINGS: tuple[tuple[str, str], ...] = (
    (r"restaurant", "locker"),
    (r"merchant", "locker"),
    (r"voucher", "rental_credit"),
    (r"dine_in", "reservation"),
    (r"dining", "rental"),
    (r"food", "inventory"),
)

_RIDE_TO_FLEET_FIELDS: dict[str, str] = {
    "driver_id": "technician_id",
    "ride_id": "work_order_id",
    "dispatch_zone": "service_zone",
    "pickup_lat": "depot_lat",
    "pickup_lng": "depot_lng",
}

_FINTECH_TO_FULFILLMENT_FIELDS: dict[str, str] = {
    "transaction_id": "shipment_id",
    "retry_count": "reship_attempt_count",
    "gateway_response_code": "carrier_status_code",
    "amount_cents": "box_value_cents",
    "processor_name": "fulfillment_partner",
    "idempotency_key": "shipment_idempotency_key",
    "payment_method": "billing_method",
}


def _rename_single_field(name: str, domain: str) -> str:
    table: dict[str, str]
    substrings: tuple[tuple[str, str], ...]
    if domain == "food_merchant":
        table, substrings = _FOOD_TO_EQUIPMENT_FIELDS, _FOOD_TO_EQUIPMENT_SUBSTRINGS
    elif domain == "ride_hailing":
        table, substrings = _RIDE_TO_FLEET_FIELDS, ()
    elif domain == "fintech":
        table, substrings = _FINTECH_TO_FULFILLMENT_FIELDS, ()
    else:
        return name

    if name in table:
        return table[name]

    result = name
    for pattern, replacement in substrings:
        result = re.sub(pattern, replacement, result, flags=re.I)
    return result


def build_field_map(field_names: list[str], domain: str) -> dict[str, str]:
    """Map original metadata column names to domain-equivalent public names."""
    if domain == "generic":
        return {}
    return {name: _rename_single_field(name, domain) for name in field_names}


def apply_field_map_to_preview(preview, field_map: dict[str, str]):
    """Apply domain column renames to a RelaxedPreview (import typed at call site)."""
    if not field_map:
        return preview

    new_relaxed: list[str] = []
    for orig, relaxed in zip(preview.original_fields, preview.relaxed_fields):
        if preview.variable_map.get(orig) == relaxed:
            # Variable synthesis already abstracted this column — keep token
            new_relaxed.append(relaxed)
        else:
            mapped = field_map.get(orig, field_map.get(relaxed, relaxed))
            new_relaxed.append(mapped)

    new_variable_map = {
        field_map.get(k, k): v for k, v in preview.variable_map.items()
    }

    return preview.model_copy(
        update={
            "relaxed_fields": new_relaxed,
            "variable_map": new_variable_map,
        }
    )


def _detect_domain(metadata: SanitizedMetadata, source_label: str, title: str) -> str:
    field_names = {f.name.lower() for f in metadata.fields}
    blob = f"{source_label} {title} {' '.join(field_names)}".lower()

    if field_names & {"merchant_id", "discovery_query", "cart_abandon", "feature_request"}:
        return "food_merchant"
    if any(t in blob for t in _FOOD_MERCHANT_TOKENS):
        return "food_merchant"
    if any(t in blob for t in _RIDE_TOKENS):
        return "ride_hailing"
    if any(t in blob for t in _FINTECH_TOKENS):
        return "fintech"
    return "generic"


def obfuscate_domain(
    metadata: SanitizedMetadata,
    source_label: str,
    title: str,
    *,
    brand_proxy: str = "StealthCo",
    sensitivity_tag: SensitivityTag | None = None,
    force: bool = False,
) -> DomainTransform | None:
    """
    Transform industry-specific intent into an equivalent but masked public narrative.

    Returns None when obfuscation is not required/applicable.
    """
    domain = _detect_domain(metadata, source_label, title)
    should_obfuscate = force or sensitivity_tag in (
        SensitivityTag.yellow,
        SensitivityTag.red,
    )
    if not should_obfuscate:
        return None

    if domain == "food_merchant":
        field_map = build_field_map([f.name for f in metadata.fields], domain)
        return DomainTransform(
            domain_proxy="hyperlocal_equipment",
            public_title="Hyperlocal Community Equipment Discovery Platform",
            public_narrative=(
                "A hyperlocal community equipment-sharing network. "
                "Users discover nearby locker inventory, reserve power tools or sporting gear, "
                "and redeem rental credits — the frontend flows mirror discovery → detail → cart "
                "but the business domain is fully masked from the original industry context."
            ),
            internal_intent=f"Internal (CTO only): {title} — {source_label}",
            transform_rationale=(
                "Food/merchant/checkout signals detected. Public challenge reframed as equipment "
                "locker discovery; metadata column names remapped (e.g. restaurant_id → locker_id)."
            ),
            brand_proxy=brand_proxy or "LockerShare",
            field_map=field_map,
        )

    if domain == "ride_hailing":
        field_map = build_field_map([f.name for f in metadata.fields], domain)
        return DomainTransform(
            domain_proxy="municipal_fleet",
            public_title="Municipal Fleet Scheduling Console",
            public_narrative=(
                "A dispatch console for municipal maintenance fleets — "
                "route assignment, geo-proximity matching, and technician handoff states."
            ),
            internal_intent=f"Internal (CTO only): {title} — {source_label}",
            transform_rationale="Ride-hailing/geo dispatch signals mapped to municipal fleet scheduling.",
            brand_proxy=brand_proxy or "CityFleet",
            field_map=field_map,
        )

    if domain == "fintech":
        field_map = build_field_map([f.name for f in metadata.fields], domain)
        return DomainTransform(
            domain_proxy="subscription_fulfillment",
            public_title="Subscription Box Fulfillment Retry Pipeline",
            public_narrative=(
                "A curated subscription box fulfillment pipeline. Students diagnose retry storms "
                "and idempotency issues in the billing pipeline."
            ),
            internal_intent=f"Internal (CTO only): {title} — {source_label}",
            transform_rationale="Payment/retry metadata abstracted to subscription fulfillment domain.",
            brand_proxy=brand_proxy or "BoxFlow",
            field_map=field_map,
        )

    # Novel industries — local LLM proposes field_map + narrative (falls back to None)
    if force or sensitivity_tag in (SensitivityTag.yellow, SensitivityTag.red):
        from . import llm_domain_obfuscator

        llm_transform = llm_domain_obfuscator.suggest_domain_transform(
            metadata,
            source_label,
            title,
            brand_proxy=brand_proxy,
            sensitivity_tag=sensitivity_tag,
        )
        if llm_transform:
            llm_transform.internal_intent = f"Internal (CTO only): {title} — {source_label}"
            return llm_transform

    return None


_FORBIDDEN_PUBLIC_TOKENS = re.compile(
    r"\b(merchant|restaurant|dine|dining|food|grab|gojek|voucher|delivery|eats)\b",
    re.I,
)


def public_text_is_safe(text: str) -> bool:
    """True when no obvious food-delivery leak tokens remain in public copy."""
    return _FORBIDDEN_PUBLIC_TOKENS.search(text) is None
