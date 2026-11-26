from typing import Dict, List, Optional
from parser import ProductRecord


def _recommendation_score(p: ProductRecord) -> float:
    """Composite score balancing rating, relevance, availability, and price."""
    avail_bonus = 1.0 if p.availability.lower() == "in stock" else 0.0
    price_factor = max(0.1, 10000.0 / max(p.price, 1.0))
    return round((p.rating * 2.0) + (p.relevance * 3.0) + avail_bonus + min(price_factor, 2.0), 3)


def filter_and_sort_products(
    records: List[ProductRecord],
    max_price: Optional[float] = None,
    min_rating: float = 0.0,
    only_in_stock: bool = False,
    sort_by: str = "price_asc",
) -> List[ProductRecord]:
    """FR6: Filter and sort products by price, rating, availability, or recommendation."""
    filtered = [
        r for r in records
        if (max_price is None or r.price <= max_price)
        and r.rating >= min_rating
        and (not only_in_stock or r.availability.lower() == "in stock")
    ]
    if sort_by == "price_asc":
        return sorted(filtered, key=lambda r: r.price)
    if sort_by == "price_desc":
        return sorted(filtered, key=lambda r: r.price, reverse=True)
    if sort_by == "rating_desc":
        return sorted(filtered, key=lambda r: (r.rating, r.reviews), reverse=True)
    if sort_by == "recommended":
        return sorted(filtered, key=_recommendation_score, reverse=True)
    return filtered


def build_comparison_matrix(grouped: Dict[str, List[ProductRecord]]) -> List[Dict]:
    """FR5 & FR8: Compare matched products side-by-side on price, rating, reviews, relevance, availability."""
    matrix = []
    for _, offers in grouped.items():
        if not offers:
            continue
        sorted_offers = sorted(offers, key=lambda o: o.price)
        best_price = sorted_offers[0]
        best_rated = max(offers, key=lambda o: (o.rating, o.reviews))
        matrix.append({
            "product_title": offers[0].title,
            "vendor_count": len(offers),
            "lowest_price": best_price.price,
            "lowest_price_vendor": best_price.source_name,
            "highest_rating": best_rated.rating,
            "highest_rating_vendor": best_rated.source_name,
            "offers": [o.to_dict() for o in sorted_offers],
        })
    return matrix


def generate_summary_digest(records: List[ProductRecord], comparison_matrix: List[Dict], failed_sources: List[Dict]) -> str:
    """FR9: Generate a concise text digest of the collected & compared information."""
    if not records:
        return "No matching products were found for the specified query and filter criteria."

    cheapest = min(records, key=lambda r: r.price)
    top_rated = max(records, key=lambda r: (r.rating, r.reviews))
    recommended = max(records, key=_recommendation_score)
    sources_used = sorted({r.source_name for r in records})

    lines = [
        f"Analyzed {len(records)} listing(s) across {len(sources_used)} website(s) ({', '.join(sources_used)}) covering {len(comparison_matrix)} unique product(s).",
        f"Best Price: '{cheapest.title}' at Rs. {cheapest.price:.0f} on {cheapest.source_name} ({cheapest.availability}).",
        f"Highest Rated: '{top_rated.title}' with {top_rated.rating} stars ({top_rated.reviews} reviews) on {top_rated.source_name}.",
        f"Overall Recommendation: '{recommended.title}' from {recommended.source_name} (Rs. {recommended.price:.0f}, {recommended.rating} stars).",
    ]
    if failed_sources:
        failed_names = ", ".join(f["name"] for f in failed_sources)
        lines.append(f"Note: {len(failed_sources)} source(s) were temporarily unreachable ({failed_names}); results were compiled from available sources.")
    return " ".join(lines)
