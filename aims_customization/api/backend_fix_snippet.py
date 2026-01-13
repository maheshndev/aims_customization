
# Check if month/year are provided but date_filter is None
if (month or year) and not date_filter:
    return []
