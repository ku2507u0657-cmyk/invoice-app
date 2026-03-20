def format_inr(amount):
    # This Unicode sequence (\u20B9) is the "native" way PDFs understand the Rupee
    return f"\u20B9{amount:,.2f}"