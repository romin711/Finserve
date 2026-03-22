def _extract_sales_history(product):
    """Return a list of sales values if the product has history-like fields."""
    sales_history = getattr(product, "sales_history", None)
    if isinstance(sales_history, list) and len(sales_history) >= 2:
        return [float(value) for value in sales_history]

    recent_sales = getattr(product, "recent_sales", None)
    previous_sales = getattr(product, "previous_sales", None)
    if recent_sales is not None and previous_sales is not None:
        return [float(previous_sales), float(recent_sales)]

    return None


def predict_future_sales(product):
    """
    Simulate AI-style demand risk prediction.

    Rules:
    - If sales trend is decreasing -> predict low demand.
    - Else -> stable demand.

    Returns one of:
    - "High Risk"
    - "Medium Risk"
    - "Low Risk"
    """
    history = _extract_sales_history(product)
    total_sales = float(getattr(product, "total_sales", 0) or 0)
    days_unsold = getattr(product, "days_unsold", None)

    if history:
        sales_trend_decreasing = history[-1] < history[0]
    else:
        # Fallback trend simulation when detailed history is not available.
        sales_trend_decreasing = total_sales < 20

    if sales_trend_decreasing:
        # Decreasing trend means low demand; longer unsold duration increases risk.
        if days_unsold is not None and days_unsold > 45:
            return "High Risk"
        if total_sales < 10:
            return "High Risk"
        return "Medium Risk"

    # Stable trend
    if days_unsold is not None and days_unsold > 30:
        return "Medium Risk"
    return "Low Risk"
