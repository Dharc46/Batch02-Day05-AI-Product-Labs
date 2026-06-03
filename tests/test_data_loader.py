from src.data_loader import get_dataset_summary, load_restaurants


def test_dataset_loads_with_minimum_size():
    restaurants = load_restaurants()

    assert len(restaurants) >= 35


def test_restaurant_ids_are_unique():
    restaurants = load_restaurants()
    ids = [restaurant.id for restaurant in restaurants]

    assert len(ids) == len(set(ids))


def test_dataset_has_required_business_coverage():
    restaurants = load_restaurants()

    assert sum(1 for item in restaurants if item.accept_voucher) >= 8
    assert sum(1 for item in restaurants if "buffet" in item.cuisine_types) >= 5
    assert (
        sum(
            1
            for item in restaurants
            if "vegetarian" in item.dietary_tags or "non_seafood_options" in item.dietary_tags
        )
        >= 5
    )
    assert len({item.brand_area for item in restaurants}) >= 6


def test_dataset_summary_runs():
    restaurants = load_restaurants()
    summary = get_dataset_summary(restaurants)

    assert summary["total_count"] == len(restaurants)
    assert summary["voucher_accepted_count"] >= 8
    assert "by_brand_area" in summary
    assert "source_status_counts" in summary
