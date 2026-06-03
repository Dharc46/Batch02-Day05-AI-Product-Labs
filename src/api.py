"""FastAPI app for the VinDine Concierge data/glue slice."""

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.data_loader import get_dataset_summary, load_restaurants
from src.mock_parser import parse_user_text_stub
from src.mock_ranking import rank_restaurants_stub
from src.schemas import (
    ApiErrorResponse,
    ClarificationQuestion,
    RecommendationRequest,
    RecommendationResponse,
    Restaurant,
)


app = FastAPI(
    title="VinDine Concierge API",
    description="Data and integration contract MVP for resort dining recommendations.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Return a consistent error shape for unexpected backend failures."""
    return JSONResponse(
        status_code=500,
        content=ApiErrorResponse(message="Internal API error", detail=str(exc)).model_dump(),
    )


def _restaurants_or_500() -> list[Restaurant]:
    try:
        return load_restaurants()
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict:
    """Report service and dataset readiness."""
    restaurants = _restaurants_or_500()
    return {
        "status": "ok",
        "service": "VinDine Concierge API",
        "dataset_loaded": True,
        "restaurant_count": len(restaurants),
    }


@app.get("/restaurants", response_model=list[Restaurant])
def list_restaurants(
    brand_area: Annotated[str | None, Query()] = None,
    accept_voucher: Annotated[bool | None, Query()] = None,
    cuisine: Annotated[str | None, Query()] = None,
    max_price: Annotated[int | None, Query(ge=0)] = None,
    stroller_accessible: Annotated[bool | None, Query()] = None,
) -> list[Restaurant]:
    """Return restaurants with optional filters for frontend exploration."""
    restaurants = _restaurants_or_500()
    if brand_area:
        restaurants = [item for item in restaurants if item.brand_area == brand_area]
    if accept_voucher is not None:
        restaurants = [item for item in restaurants if item.accept_voucher is accept_voucher]
    if cuisine:
        restaurants = [item for item in restaurants if cuisine in item.cuisine_types]
    if max_price is not None:
        restaurants = [item for item in restaurants if item.avg_price_vnd <= max_price]
    if stroller_accessible is not None:
        restaurants = [item for item in restaurants if item.stroller_accessible is stroller_accessible]
    return restaurants


@app.get("/dataset/summary")
def dataset_summary() -> dict:
    """Return aggregate counts proving the dataset is diverse enough for demos."""
    return get_dataset_summary(_restaurants_or_500())


def _clarification_questions(request: RecommendationRequest, confidence: float) -> list[ClarificationQuestion]:
    questions: list[ClarificationQuestion] = []
    if not request.current_zone and confidence < 0.6:
        questions.append(
            ClarificationQuestion(
                id="current_zone",
                question="Bạn đang ở khu/sảnh nào trong Vin?",
                options=["Cổng chính", "Sảnh resort", "Harbour", "Food Court"],
            )
        )
    if "voucher" in request.user_text.lower() and not request.voucher_type:
        questions.append(
            ClarificationQuestion(
                id="voucher_type",
                question="Voucher của bạn là buffet, meal credit hay discount?",
                options=["buffet", "meal_credit", "combo", "discount"],
            )
        )
    return questions[:2]


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(request: RecommendationRequest) -> RecommendationResponse:
    """Parse a group request, rank restaurants, and return cards or fallback guidance."""
    restaurants = _restaurants_or_500()
    parsed_constraints = parse_user_text_stub(request)
    recommendations, fallback_suggestions = rank_restaurants_stub(restaurants, parsed_constraints)
    clarification_questions = _clarification_questions(request, parsed_constraints.confidence)

    if not recommendations:
        status = "no_match"
    elif parsed_constraints.confidence < 0.6 or clarification_questions:
        status = "needs_clarification"
    else:
        status = "success"

    return RecommendationResponse(
        status=status,
        parsed_constraints=parsed_constraints,
        clarification_questions=clarification_questions,
        recommendations=recommendations,
        fallback_suggestions=fallback_suggestions,
        debug={
            "parser": "parse_user_text_stub",
            "ranker": "rank_restaurants_stub",
            "restaurant_count": len(restaurants),
        },
    )
