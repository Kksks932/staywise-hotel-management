import os
from datetime import date
from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-development-key")

def get_db_connection():
    """Create a fresh MySQL connection using environment variables."""
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", "12887")),
        ssl_disabled=False
    )

def fetch_all(query, params=()):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def execute_query(query, params=()):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()

@app.route("/")
def dashboard():
    stats = {}
    for key, query in {
        "customers": "SELECT COUNT(*) AS n FROM customers",
        "rooms": "SELECT COUNT(*) AS n FROM rooms",
        "bookings": "SELECT COUNT(*) AS n FROM bookings",
        "active_bookings": "SELECT COUNT(*) AS n FROM bookings WHERE status IN ('Booked','Checked-in')"
    }.items():
        rows = fetch_all(query)
        stats[key] = rows[0]["n"]
    recent = fetch_all("""
        SELECT b.booking_id, c.name AS customer_name, r.room_number,
               b.check_in, b.check_out, b.status
        FROM bookings b
        JOIN customers c ON c.customer_id = b.customer_id
        JOIN rooms r ON r.room_id = b.room_id
        ORDER BY b.booking_id DESC LIMIT 5
    """)
    return render_template("dashboard.html", stats=stats, recent=recent)

# ---------------- Customers: CRUD ----------------
@app.route("/customers")
def customers():
    rows = fetch_all("SELECT * FROM customers ORDER BY customer_id DESC")
    return render_template("customers.html", customers=rows)

@app.route("/customers/add", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        if not name:
            flash("Customer name is required.", "error")
            return render_template("customer_form.html", customer=None)
        execute_query(
            "INSERT INTO customers (name, phone, email, address) VALUES (%s,%s,%s,%s)",
            (name, phone or None, email or None, address or None)
        )
        flash("Customer added successfully.", "success")
        return redirect(url_for("customers"))
    return render_template("customer_form.html", customer=None)

@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    rows = fetch_all("SELECT * FROM customers WHERE customer_id = %s", (customer_id,))
    if not rows:
        flash("Customer not found.", "error")
        return redirect(url_for("customers"))
    customer = rows[0]
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Customer name is required.", "error")
            return render_template("customer_form.html", customer=customer)
        execute_query("""
            UPDATE customers SET name=%s, phone=%s, email=%s, address=%s
            WHERE customer_id=%s
        """, (
            name, request.form.get("phone", "").strip() or None,
            request.form.get("email", "").strip() or None,
            request.form.get("address", "").strip() or None, customer_id
        ))
        flash("Customer updated successfully.", "success")
        return redirect(url_for("customers"))
    return render_template("customer_form.html", customer=customer)

@app.post("/customers/<int:customer_id>/delete")
def delete_customer(customer_id):
    try:
        execute_query("DELETE FROM customers WHERE customer_id=%s", (customer_id,))
        flash("Customer deleted.", "success")
    except Error:
        flash("This customer has bookings. Delete or reassign their bookings first.", "error")
    return redirect(url_for("customers"))

# ---------------- Rooms: CRUD ----------------
@app.route("/rooms")
def rooms():
    rows = fetch_all("SELECT * FROM rooms ORDER BY room_number")
    return render_template("rooms.html", rooms=rows)

@app.route("/rooms/add", methods=["GET", "POST"])
def add_room():
    if request.method == "POST":
        room_number = request.form.get("room_number", "").strip()
        room_type = request.form.get("room_type", "").strip()
        price = request.form.get("price_per_night", "").strip()
        status = request.form.get("status", "Available")
        try:
            price = float(price)
            if not room_number or price < 0:
                raise ValueError()
            execute_query("""
                INSERT INTO rooms (room_number, room_type, price_per_night, status)
                VALUES (%s,%s,%s,%s)
            """, (room_number, room_type, price, status))
            flash("Room added successfully.", "success")
            return redirect(url_for("rooms"))
        except ValueError:
            flash("Enter a room number and a valid non-negative price.", "error")
        except Error:
            flash("Could not add room. The room number may already exist.", "error")
    return render_template("room_form.html", room=None)

@app.route("/rooms/<int:room_id>/edit", methods=["GET", "POST"])
def edit_room(room_id):
    rows = fetch_all("SELECT * FROM rooms WHERE room_id=%s", (room_id,))
    if not rows:
        flash("Room not found.", "error")
        return redirect(url_for("rooms"))
    room = rows[0]
    if request.method == "POST":
        try:
            price = float(request.form.get("price_per_night", ""))
            if price < 0:
                raise ValueError()
            execute_query("""
                UPDATE rooms SET room_number=%s, room_type=%s, price_per_night=%s, status=%s
                WHERE room_id=%s
            """, (
                request.form.get("room_number", "").strip(),
                request.form.get("room_type", "").strip(), price,
                request.form.get("status", "Available"), room_id
            ))
            flash("Room updated successfully.", "success")
            return redirect(url_for("rooms"))
        except ValueError:
            flash("Enter a valid non-negative price.", "error")
        except Error:
            flash("Could not update room. Check the room number and existing bookings.", "error")
    return render_template("room_form.html", room=room)

@app.post("/rooms/<int:room_id>/delete")
def delete_room(room_id):
    try:
        execute_query("DELETE FROM rooms WHERE room_id=%s", (room_id,))
        flash("Room deleted.", "success")
    except Error:
        flash("This room has booking records. Cancel/remove those bookings first.", "error")
    return redirect(url_for("rooms"))

# ---------------- Bookings: CRUD ----------------
@app.route("/bookings")
def bookings():
    rows = fetch_all("""
        SELECT b.*, c.name AS customer_name, r.room_number, r.room_type
        FROM bookings b
        JOIN customers c ON c.customer_id=b.customer_id
        JOIN rooms r ON r.room_id=b.room_id
        ORDER BY b.booking_id DESC
    """)
    return render_template("bookings.html", bookings=rows)

@app.route("/bookings/add", methods=["GET", "POST"])
def add_booking():
    customer_rows = fetch_all("SELECT customer_id, name FROM customers ORDER BY name")
    room_rows = fetch_all("SELECT room_id, room_number, room_type, price_per_night FROM rooms ORDER BY room_number")
    if request.method == "POST":
        try:
            customer_id = int(request.form["customer_id"])
            room_id = int(request.form["room_id"])
            check_in = date.fromisoformat(request.form["check_in"])
            check_out = date.fromisoformat(request.form["check_out"])
            if check_out <= check_in:
                raise ValueError("Check-out must be after check-in.")
            # Prevent overlapping reservations for the same room.
            overlaps = fetch_all("""
                SELECT booking_id FROM bookings
                WHERE room_id=%s AND status IN ('Booked','Checked-in')
                  AND check_in < %s AND check_out > %s
            """, (room_id, check_out, check_in))
            if overlaps:
                flash("That room is already booked for some of those dates.", "error")
                return render_template("booking_form.html", customers=customer_rows, rooms=room_rows)
            execute_query("""
                INSERT INTO bookings (customer_id, room_id, check_in, check_out, status)
                VALUES (%s,%s,%s,%s,'Booked')
            """, (customer_id, room_id, check_in, check_out))
            flash("Booking created successfully.", "success")
            return redirect(url_for("bookings"))
        except (ValueError, KeyError):
            flash("Choose a customer and room, and enter valid dates (check-out after check-in).", "error")
    return render_template("booking_form.html", customers=customer_rows, rooms=room_rows)

@app.route("/bookings/<int:booking_id>/edit", methods=["GET", "POST"])
def edit_booking(booking_id):
    rows = fetch_all("SELECT * FROM bookings WHERE booking_id=%s", (booking_id,))
    if not rows:
        flash("Booking not found.", "error")
        return redirect(url_for("bookings"))
    booking = rows[0]
    customer_rows = fetch_all("SELECT customer_id, name FROM customers ORDER BY name")
    room_rows = fetch_all("SELECT room_id, room_number, room_type, price_per_night FROM rooms ORDER BY room_number")
    if request.method == "POST":
        try:
            customer_id = int(request.form["customer_id"])
            room_id = int(request.form["room_id"])
            check_in = date.fromisoformat(request.form["check_in"])
            check_out = date.fromisoformat(request.form["check_out"])
            status = request.form["status"]
            if check_out <= check_in:
                raise ValueError()
            overlaps = fetch_all("""
                SELECT booking_id FROM bookings
                WHERE room_id=%s AND booking_id<>%s
                  AND status IN ('Booked','Checked-in')
                  AND check_in < %s AND check_out > %s
            """, (room_id, booking_id, check_out, check_in))
            if overlaps and status in ("Booked", "Checked-in"):
                flash("That room is already booked for some of those dates.", "error")
                return render_template("booking_edit.html", booking=booking, customers=customer_rows, rooms=room_rows)
            execute_query("""
                UPDATE bookings
                SET customer_id=%s, room_id=%s, check_in=%s, check_out=%s, status=%s
                WHERE booking_id=%s
            """, (customer_id, room_id, check_in, check_out, status, booking_id))
            flash("Booking updated successfully.", "success")
            return redirect(url_for("bookings"))
        except (ValueError, KeyError):
            flash("Enter valid booking details and dates.", "error")
    return render_template("booking_edit.html", booking=booking, customers=customer_rows, rooms=room_rows)

@app.post("/bookings/<int:booking_id>/delete")
def delete_booking(booking_id):
    execute_query("DELETE FROM bookings WHERE booking_id=%s", (booking_id,))
    flash("Booking record deleted.", "success")
    return redirect(url_for("bookings"))

@app.errorhandler(Error)
def handle_db_error(error):
    return render_template("error.html", message="A database error occurred. Check your MySQL settings and ensure schema.sql has been imported.", detail=str(error)), 500

if __name__ == "__main__":
    app.run(debug=True)
