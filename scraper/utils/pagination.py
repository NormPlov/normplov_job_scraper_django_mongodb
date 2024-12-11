def paginate_query(queryset, page, page_size):
    
    total_items = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size

    paginated_data = queryset[start:end]
    total_pages = (total_items + page_size - 1) // page_size

    meta = {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages
    }

    return {"data": paginated_data, "meta": meta}
