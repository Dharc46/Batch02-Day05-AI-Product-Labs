# Person 1 Data + Glue: VinDine Concierge

This slice provides the shared dataset, Pydantic contracts, FastAPI endpoints, and parser/ranking stubs for the VinDine Concierge MVP.

## Run API

```bash
pip install -r requirements.txt
uvicorn src.api:app --reload
```

Open FastAPI docs at `http://127.0.0.1:8000/docs`.

## Test

```bash
pytest
```

## Dataset

`data/vin_restaurants.json` contains 36 realistic mock/synthetic dining records across:

- VinWonders Nha Trang
- Vinpearl Harbour Nha Trang
- Vinpearl Resort Nha Trang / Hon Tre Island
- VinWonders Phu Quoc
- Grand World / Vinpearl Phu Quoc area
- VinWonders Nam Hoi An

The dataset is not an official complete Vinpearl directory. Records with `source_status = "verified_name"` only use public-style name/area anchors; price, accessibility, voucher, distance, menu, and suitability fields are modeled for MVP testing unless explicitly verified later.

## API Contract

Key models live in `src/schemas.py`:

- `Restaurant`
- `RecommendationRequest`
- `ParsedConstraints`
- `RecommendationCard`
- `RecommendationResponse`
- `ClarificationQuestion`
- `ApiErrorResponse`

## Endpoints

- `GET /health`: service and dataset readiness.
- `GET /restaurants`: optional filters `brand_area`, `accept_voucher`, `cuisine`, `max_price`, `stroller_accessible`.
- `GET /dataset/summary`: aggregate counts for dataset quality checks.
- `POST /recommend`: parse request, rank Top 3, or return clarification/fallback.

## Example `/recommend`

Request:

```json
{
  "user_text": "Nhóm 6 người ở sảnh chính, có ông bà và trẻ con, có voucher buffet, muốn món Việt hoặc pizza, cần xe đẩy",
  "current_zone": "sảnh chính",
  "voucher_type": "buffet",
  "party_size": 6,
  "correction": null
}
```

Response shape:

```json
{
  "status": "success",
  "parsed_constraints": {},
  "clarification_questions": [],
  "recommendations": [
    {
      "restaurant_id": "gateway-restaurant",
      "name": "Gateway Restaurant",
      "fit_score": 130,
      "rank": 1,
      "reasons": ["Khớp voucher yêu cầu"],
      "trade_offs": []
    }
  ],
  "fallback_suggestions": [],
  "debug": {}
}
```

## Integration Notes

Person 2 can replace `parse_user_text_stub(request)` in `src/mock_parser.py` as long as it returns `ParsedConstraints`.

Person 3 can replace `rank_restaurants_stub(restaurants, constraints)` in `src/mock_ranking.py` as long as it returns `(list[RecommendationCard], list[str])`.

The UI can integrate against `POST /recommend` immediately. Even low-confidence requests return parsed constraints and may include recommendation cards plus clarification questions.
