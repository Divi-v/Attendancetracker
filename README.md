#**Employee Attendance System**
This is a simple and intuitive web application for tracking employee punch-in and punch-out times. The app records attendance, flags late arrivals and early departures, and calculates extra hours worked.

#**Features**
Employee-centric Tracking: Log attendance using employee names instead of IDs.

Automated Time Logging: Records real-time punch-in and punch-out times.

IST Time Zone: All time logging is set to Indian Standard Time (IST).

Attendance Status: Automatically flags punch-ins after 10:15 AM as "Late" and punch-outs before 6:45 PM as "Early Out."

Extra Hour Calculation: Calculates extra hours worked after 7:00 PM.

Data Persistence: Uses a local SQLite database to store all attendance records.

Data Export: Allows users to download all attendance data as a Microsoft Excel file (.xlsx).

#**How to Use**
Enter your name in the text box.

Click the "Punch In" button when you arrive at work.

Click the "Punch Out" button when you leave.

The attendance table below will update automatically.

Use the "Export to Excel" button to download the complete records.

#**Technologies Used**
Streamlit: The Python framework used to create the web application.

Python: The core programming language.

SQLite: A lightweight, file-based database for data storage.

Pandas: Used for data manipulation and exporting to Excel.

xlsxwriter: The engine used by Pandas for creating Excel files.

pytz: For handling time zone conversions to IST.
