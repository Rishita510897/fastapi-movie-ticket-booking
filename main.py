from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import List, Optional

app = FastAPI()

# DATA

movies = [
    {"id": 1, "title": "Leo", "genre": "Action", "language": "Tamil", "duration_mins": 160, "ticket_price": 200, "seats_available": 50},
    {"id": 2, "title": "Salaar", "genre": "Action", "language": "Telugu", "duration_mins": 170, "ticket_price": 250, "seats_available": 40},
    {"id": 3, "title": "RRR", "genre": "Drama", "language": "Telugu", "duration_mins": 180, "ticket_price": 300, "seats_available": 60},
    {"id": 4, "title": "Jawan", "genre": "Action", "language": "Hindi", "duration_mins": 150, "ticket_price": 220, "seats_available": 35},
    {"id": 5, "title": "KGF", "genre": "Drama", "language": "Kannada", "duration_mins": 155, "ticket_price": 240, "seats_available": 45},
    {"id": 6, "title": "It", "genre": "Horror", "language": "English", "duration_mins": 140, "ticket_price": 180, "seats_available": 30},
]

bookings = []
booking_counter = 1

holds = []
hold_counter = 1

# MODELS

class BookingRequest(BaseModel):
    customer_name: str = Field(min_length=2)
    movie_id: int = Field(gt=0)
    seats: int = Field(gt=0, le=10)
    phone: str = Field(min_length=10)
    seat_type: str = "standard"
    promo_code: str = ""

class NewMovie(BaseModel):
    title: str = Field(min_length=2)
    genre: str = Field(min_length=2)
    language: str = Field(min_length=2)
    duration_mins: int = Field(gt=0)
    ticket_price: int = Field(gt=0)
    seats_available: int = Field(gt=0)


# HELPER FUNCTIONS

def find_movie(movie_id):
    return next((m for m in movies if m["id"] == movie_id), None)

def calculate_ticket_cost(price, seats, seat_type, promo_code):
    multiplier = 1
    if seat_type == "premium":
        multiplier = 1.5
    elif seat_type == "recliner":
        multiplier = 2

    original = price * seats * multiplier

    discount = 0
    if promo_code == "SAVE10":
        discount = 0.1
    elif promo_code == "SAVE20":
        discount = 0.2

    final = original * (1 - discount)

    return original, final

def filter_movies_logic(genre, language, max_price, min_seats):
    result = movies
    if genre is not None:
        result = [m for m in result if m["genre"].lower() == genre.lower()]
    if language is not None:
        result = [m for m in result if m["language"].lower() == language.lower()]
    if max_price is not None:
        result = [m for m in result if m["ticket_price"] <= max_price]
    if min_seats is not None:
        result = [m for m in result if m["seats_available"] >= min_seats]
    return result


@app.get("/")
def home():
    return {"message": "Welcome to CineStar Booking"}

@app.get("/movies/search")
def search_movies(keyword: str):
    result = [m for m in movies if keyword.lower() in m["title"].lower()
              or keyword.lower() in m["genre"].lower()
              or keyword.lower() in m["language"].lower()]

    if not result:
        return {"message": "No movies found"}

    return {"results": result, "total_found": len(result)}


@app.get("/movies/filter")
def filter_movies(
    genre: Optional[str] = None,
    language: Optional[str] = None,
    max_price: Optional[int] = None,
    min_seats: Optional[int] = None
):
    return filter_movies_logic(genre, language, max_price, min_seats)


@app.get("/movies/sort")
def sort_movies(sort_by: str = "ticket_price"):
    return sorted(movies, key=lambda x: x[sort_by])


@app.get("/movies/page")
def get_movies_page(page: int = Query(1, ge=1), limit: int = Query(3, ge=1)):
    # Your logic to fetch `page` of movies
    total_movies = len(movies)  # assume movies is your list
    start = (page - 1) * limit
    end = start + limit
    data = movies[start:end]
    total_pages = (len(movies) + limit - 1) // limit
    return {
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "data": data
    }


@app.get("/movies/browse")
def browse_movies(
    keyword: Optional[str] = None,
    genre: Optional[str] = None,
    language: Optional[str] = None,
    sort_by: str = "ticket_price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):
    result = movies

    if keyword:
        result = [m for m in result if keyword.lower() in m["title"].lower()]

    if genre:
        result = [m for m in result if m["genre"].lower() == genre.lower()]

    if language:
        result = [m for m in result if m["language"].lower() == language.lower()]

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == "desc"))

    start = (page - 1) * limit
    end = start + limit

    return {
        "total": len(result),
        "data": result[start:end]
    }


@app.get("/movies")
def get_movies():
    return {
        "movies": movies,
        "total": len(movies),
        "total_seats_available": sum(m["seats_available"] for m in movies)
    }

@app.get("/movies/summary")
def summary():
    return {
        "total_movies": len(movies),
        "most_expensive": max(movies, key=lambda x: x["ticket_price"]),
        "cheapest": min(movies, key=lambda x: x["ticket_price"]),
        "total_seats": sum(m["seats_available"] for m in movies),
        "genre_count": {g: len([m for m in movies if m["genre"] == g]) for g in set(m["genre"] for m in movies)}
    }

@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie

@app.get("/bookings")
def get_bookings():
    return {
        "bookings": bookings,
        "total": len(bookings),
        "total_revenue": sum(b["final_cost"] for b in bookings)
    }


@app.post("/bookings")
def create_booking(data: BookingRequest):
    global booking_counter

    movie = find_movie(data.movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    if movie["seats_available"] < data.seats:
        raise HTTPException(400, "Not enough seats")

    original, final = calculate_ticket_cost(
        movie["ticket_price"],
        data.seats,
        data.seat_type,
        data.promo_code
    )

    movie["seats_available"] -= data.seats

    booking = {
        "booking_id": booking_counter,
        "customer_name": data.customer_name,
        "movie_title": movie["title"],
        "seats": data.seats,
        "seat_type": data.seat_type,
        "original_cost": original,
        "final_cost": final
    }

    bookings.append(booking)
    booking_counter += 1

    return booking



@app.post("/movies", status_code=201)
def add_movie(movie: NewMovie):
    if any(m["title"].lower() == movie.title.lower() for m in movies):
        raise HTTPException(400, "Duplicate movie")

    new = movie.dict()
    new["id"] = len(movies) + 1
    movies.append(new)
    return new

@app.put("/movies/{movie_id}")
def update_movie(movie_id: int,
                 ticket_price: Optional[int] = None,
                 seats_available: Optional[int] = None):

    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(404, "Not found")
    if ticket_price is None and seats_available is None:
        raise HTTPException(400, "No fields to update")

    if ticket_price is not None:
        movie["ticket_price"] = ticket_price
    if seats_available is not None:
        movie["seats_available"] = seats_available
    return {
    "message": "Movie updated successfully",
    "data": movie
}
    

@app.delete("/movies/{movie_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie:
        raise HTTPException(404, "Not found")

    if any(b["movie_title"] == movie["title"] for b in bookings):
        raise HTTPException(400, "Movie has bookings")

    movies.remove(movie)
    return {"message": "Movie Deleted successfully"}


@app.post("/seat-hold")
def seat_hold(data: BookingRequest):
    global hold_counter

    movie = find_movie(data.movie_id)
    if not movie:
        raise HTTPException(404, "Movie not found")

    if movie["seats_available"] < data.seats:
        raise HTTPException(400, "Not enough seats")

    movie["seats_available"] -= data.seats

    hold = {
        "hold_id": hold_counter,
        "movie_id": data.movie_id,
        "seats": data.seats,
        "customer_name": data.customer_name
    }

    holds.append(hold)
    hold_counter += 1

    return hold

@app.get("/seat-hold")
def get_holds():
    return holds

@app.post("/seat-confirm/{hold_id}")
def confirm_hold(hold_id: int):
    global booking_counter

    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(404, "Hold not found")

    movie = find_movie(hold["movie_id"])

    booking = {
        "booking_id": booking_counter,
        "customer_name": hold["customer_name"],
        "movie_title": movie["title"],
        "seats": hold["seats"],
        "final_cost": hold["seats"] * movie["ticket_price"]
    }

    bookings.append(booking)
    holds.remove(hold)
    booking_counter += 1

    return booking

@app.delete("/seat-release/{hold_id}")
def release_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold:
        raise HTTPException(404, "Hold not found")

    movie = find_movie(hold["movie_id"])
    movie["seats_available"] += hold["seats"]

    holds.remove(hold)
    return {"message": "Released"}




