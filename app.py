
import streamlit as st
import sqlite3
import datetime
import pandas as pd
from pytz import timezone
from io import BytesIO

# Define the database file name
DB_FILE = 'attendance.db'

# --- Database Functions ---
def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    except sqlite3.Error as e:
        st.error(f"Error connecting to database: {e}")
    return conn

def create_table(conn):
    """Create the attendance table, handling column changes."""
    try:
        cursor = conn.cursor()
        
        # Check if the old table with employee_id exists
        cursor.execute("PRAGMA table_info(attendance)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'employee_id' in columns:
            cursor.execute("DROP TABLE attendance;")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                employee_name TEXT PRIMARY KEY,
                punch_in_date DATE,
                punch_in_time TIME,
                punch_out_time TIME NULL,
                status TEXT,
                extra_hours REAL
            );
        """)
        conn.commit()
    except sqlite3.Error as e:
        st.error(f"Error creating table: {e}")

def record_punch_in(conn, employee_name, punch_in_date, punch_in_time, status):
    """Record a punch-in for an employee."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO attendance (employee_name, punch_in_date, punch_in_time, status)
            VALUES (?, ?, ?, ?);
        """, (employee_name, punch_in_date, punch_in_time, status))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error recording punch-in: {e}")
        return False

def record_punch_out(conn, employee_name, punch_out_date, punch_out_time, status, extra_hours):
    """Update a record with punch-out time and extra hours."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE attendance
            SET punch_out_time = ?, status = ?, extra_hours = ?
            WHERE employee_name = ? AND punch_in_date = ?;
        """, (punch_out_time, status, extra_hours, employee_name, punch_out_date))
        conn.commit()
        return True
    except sqlite3.Error as e:
        st.error(f"Error recording punch-out: {e}")
        return False

def get_employee_record_today(conn, employee_name, current_date):
    """Fetch an employee's record for the current day."""
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM attendance
            WHERE employee_name = ? AND punch_in_date = ?;
        """, (employee_name, current_date))
        return cursor.fetchone()
    except sqlite3.Error as e:
        st.error(f"Error fetching record: {e}")
        return None

def get_all_records(conn):
    """Fetch all attendance records."""
    try:
        df = pd.read_sql_query("SELECT * FROM attendance", conn)
        return df
    except sqlite3.Error as e:
        st.error(f"Error fetching all records: {e}")
        return pd.DataFrame()

# --- Main Streamlit App Logic ---
def main():
    st.title("Employee Attendance System ⏰")
    st.markdown("---")

    conn = create_connection()
    if conn is not None:
        create_table(conn)

        # --- Input Section ---
        employee_name = st.text_input("Enter your Name", help="e.g., Jane Doe")

        col1, col2 = st.columns(2)
        
        with col1:
            punch_in_btn = st.button("Punch In")

        with col2:
            punch_out_btn = st.button("Punch Out")

        # Set time zone to IST
        ist_zone = timezone('Asia/Kolkata')
        
        # --- Punch In Logic ---
        if punch_in_btn:
            if not employee_name:
                st.warning("Please enter your Name.")
            else:
                current_ist_time = datetime.datetime.now(ist_zone)
                current_date = current_ist_time.date().isoformat()
                current_time = current_ist_time.time().isoformat()
                
                # Check if employee has already punched in today
                record = get_employee_record_today(conn, employee_name, current_date)
                
                if record:
                    st.warning(f"{employee_name}, you have already punched in today.")
                else:
                    # Define late punch-in buffer (10:00 AM - 10:15 AM)
                    late_buffer_time = datetime.time(10, 15)
                    punch_time_dt = current_ist_time.time()

                    status = "On Time" if punch_time_dt <= late_buffer_time else "Late"

                    if record_punch_in(conn, employee_name, current_date, current_time, status):
                        if status == "On Time":
                            st.success(f"Punch In Successful for {employee_name} at {current_time}! Status: {status}")
                        else:
                            st.error(f"Punch In Successful for {employee_name} at {current_time}! Status: {status}")

        # --- Punch Out Logic ---
        if punch_out_btn:
            if not employee_name:
                st.warning("Please enter your Name.")
            else:
                current_ist_time = datetime.datetime.now(ist_zone)
                current_date = current_ist_time.date().isoformat()
                current_time = current_ist_time.time().isoformat()

                # Get today's punch-in record
                record = get_employee_record_today(conn, employee_name, current_date)

                if not record:
                    st.warning("You have not punched in yet today. Please punch in first.")
                else:
                    # Unpack the record (fixed indexing to get the correct punch_in_time)
                    _, _, punch_in_time_str, punch_out_time_str, _, _ = record
                    
                    if punch_out_time_str: # Check if punch-out time is already set
                        st.warning(f"{employee_name}, you have already punched out today.")
                        return

                    # Convert times to datetime objects for calculation
                    punch_in_dt_utc = datetime.datetime.strptime(punch_in_time_str.split('.')[0], "%H:%M:%S")
                    
                    # Define time buffers
                    early_out_buffer = datetime.time(18, 45)  # 6:45 PM
                    extra_hours_buffer = datetime.time(19, 0)  # 7:00 PM

                    punch_out_time_dt = current_ist_time.time()
                    status = "On Time"
                    extra_hours = 0.0

                    if punch_out_time_dt < early_out_buffer:
                        status = "Early Out"
                        st.warning(f"Punch Out Successful for {employee_name} at {current_time}! Status: {status}")
                    elif punch_out_time_dt > extra_hours_buffer:
                        status = "On Time" # Status remains On Time
                        # Calculate extra hours
                        extra_time = current_ist_time - current_ist_time.replace(hour=19, minute=0, second=0, microsecond=0)
                        extra_hours = extra_time.total_seconds() / 3600
                        st.info(f"You have worked an extra {extra_hours:.2f} hours!")
                        st.success(f"Punch Out Successful for {employee_name} at {current_time}! Status: {status}")
                    else:
                        st.success(f"Punch Out Successful for {employee_name} at {current_time}! Status: {status}")

                    record_punch_out(conn, employee_name, current_date, current_time, status, extra_hours)

        st.markdown("---")
        st.subheader("Attendance Records")
        df_records = get_all_records(conn)
        if not df_records.empty:
            st.dataframe(df_records)

            # Add a download button for the Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_records.to_excel(writer, index=False, sheet_name='Attendance')
            st.download_button(
                label="Export to Excel",
                data=output.getvalue(),
                file_name="attendance_records.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.info("No records to display yet.")
    
    conn.close()

if __name__ == "__main__":
    main()
