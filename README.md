# 🎬 FastAPI Movie Ticket Booking

A **FastAPI backend** for cinema ticket booking.  
Features GET/POST endpoints, Pydantic validation, helper functions, CRUD operations, multi-step workflows, search, sort, pagination, and combined browse logic.

---

##  Features

- Browse movies: search, filter, sort, pagination  
- Book seats with promo codes  
- Seat workflow: hold → confirm → release  
- CRUD operations on movies  
- Summary & analytics endpoints  

---

##  Project Structure
movie-ticket-booking/
├── main.py
├── requirements.txt
├── README.md
└── screenshots/

##  Endpoints (Q1–Q20)

- **Q1–Q5:** Home, list movies, get by ID, bookings, summary  
- **Q6–Q10:** Booking request, helper functions, POST bookings, promo code, filter  
- **Q11–Q13:** CRUD: add, update, delete movies  
- **Q14–Q15:** Seat hold workflow  
- **Q16–Q20:** Search, sort, pagination, combined `/browse` endpoint  

## Run Locally

```bash
git clone https://github.com/YourUsername/fastapi-movie-ticket-booking.git
cd fastapi-movie-ticket-booking
pip install -r requirements.txt
uvicorn main:app --reload
