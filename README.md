# Hotel Management System (Flask + MySQL)

A basic college DBMS project with a browser interface and CRUD operations for customers, rooms, and bookings.

## Requirements
- Python 3.10+
- MySQL Server
- A browser

## Setup

1. Install Python and MySQL Server. Start the MySQL service.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment:

   **Windows**
   ```bat
   py -m venv .venv
   .venv\Scripts\activate
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create the database and tables. In MySQL Workbench, open `schema.sql` and execute it. Alternatively:
   ```bash
   mysql -u root -p < schema.sql
   ```
   Enter your MySQL password when prompted.

6. Set your database connection details in the terminal before running the app.

   **Windows Command Prompt**
   ```bat
   set DB_HOST=localhost
   set DB_USER=root
   set DB_PASSWORD=your_actual_mysql_password
   set DB_NAME=hotel_management
   ```

   **Windows PowerShell**
   ```powershell
   $env:DB_HOST="localhost"
   $env:DB_USER="root"
   $env:DB_PASSWORD="your_actual_mysql_password"
   $env:DB_NAME="hotel_management"
   ```

   **macOS/Linux**
   ```bash
   export DB_HOST=localhost
   export DB_USER=root
   export DB_PASSWORD='your_actual_mysql_password'
   export DB_NAME=hotel_management
   ```

7. Start the application:
   ```bash
   python app.py
   ```

8. Open `http://127.0.0.1:5000` in your browser.

## Demonstration flow
1. Add a customer.
2. Add a room (or use the sample rooms created by `schema.sql`).
3. Create a booking for that customer and room.
4. Edit a customer, room, or booking to demonstrate UPDATE.
5. Delete a record without linked bookings to demonstrate DELETE.
6. Try overlapping dates for the same room to demonstrate booking validation.

## Tables and relationships
- `customers`: one customer can have many bookings.
- `rooms`: one room can have many bookings over time.
- `bookings`: each booking references one customer and one room.

## Notes
- The app is intended for a local college demonstration, not production use.
- The booking form prevents overlapping bookings for the same room when the existing booking is Booked or Checked-in.
- Room status is maintained as a room-level label; date-based availability is determined from booking dates.
- For production deployment, disable Flask debug mode, use a strong secret key, add authentication/authorization, CSRF protection, and stronger transaction/concurrency handling.
