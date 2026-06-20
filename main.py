import sqlite3
import os
from datetime import date
import hashlib
from getpass import getpass

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

#Database Query and Connection

def connect_db(): 
    conn = sqlite3.connect("expenses.db")
    cur = conn.cursor()
    return conn, cur


def create_tables():
    conn, cur = connect_db()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            monthly_budget REAL DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL
        )
    """)

    conn.commit()
    conn.close()


#Authorization
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register(u, p):
    conn, cur = connect_db()
    try:
        hashed_pw = hash_password(p)
        cur.execute("INSERT INTO users(username,password) VALUES(?,?)", (u, hashed_pw))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login(u, p):
    conn, cur = connect_db()
    hashed_pw = hash_password(p)
    
    cur.execute("SELECT id FROM users WHERE username=? AND password=?", (u, hashed_pw))
    user = cur.fetchone()
    conn.close()
    return user[0] if user else None



#Expense Functions  

def add_expense(uid, d, c, desc, amt):
    conn, cur = connect_db()
    cur.execute("""
        INSERT INTO expenses(user_id,date,category,description,amount)
        VALUES(?,?,?,?,?)
    """, (uid, d, c, desc, amt))
    conn.commit()
    conn.close()


def fetch_all(uid):
    conn, cur = connect_db()
    cur.execute("""
        SELECT id,date,category,description,amount
        FROM expenses
        WHERE user_id=?
        ORDER BY id DESC
    """, (uid,))
    data = cur.fetchall()
    conn.close()
    return data


def total(uid):
    conn, cur = connect_db()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM expenses WHERE user_id=?", (uid,))
    t = cur.fetchone()[0]
    conn.close()
    return t



def delete(exp_id):
    conn, cur = connect_db()

    cur.execute("DELETE FROM expenses WHERE id=?", (exp_id,))

    if cur.rowcount > 0:
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False


def update(exp_id, d, c, desc, amt):
    conn, cur = connect_db()
    cur.execute("""
        UPDATE expenses
        SET date=?, category=?, description=?, amount=?
        WHERE id=?
    """, (d, c, desc, amt, exp_id))
    conn.commit()
    conn.close()


def search(uid, keyword):
    conn, cur = connect_db()
    cur.execute("""
        SELECT id,date,category,description,amount
        FROM expenses
        WHERE user_id=? AND category LIKE ?
    """, (uid, "%" + keyword + "%"))
    data = cur.fetchall()
    conn.close()
    return data



# BUDGET SYSTEM + SMART ADVISOR


def set_budget(uid, amount):
    conn, cur = connect_db()
    cur.execute("UPDATE users SET monthly_budget=? WHERE id=?", (amount, uid))
    conn.commit()
    conn.close()


def get_budget(uid):
    
    conn, cur = connect_db()
    cur.execute("SELECT COALESCE(monthly_budget,0) FROM users WHERE id=?", (uid,))
    b = cur.fetchone()[0]
    conn.close()
    return b


def smart_budget_advisor(uid):
    b = get_budget(uid)
    t = total(uid)

    print("\n========== SMART BUDGET ADVISOR ==========")

    if b == 0:
        print("⚠ No budget set. Set budget to get insights.")
        return

    remaining = b - t
    percent = (t / b) * 100

    print(f"Budget     : Rs {b}")
    print(f"Spent      : Rs {t}")
    print(f"Remaining  : Rs {remaining}")

    if t > b:
        print("ALERT: You are OVER BUDGET!")
        print("Advice: Stop unnecessary spending immediately.")
    elif percent >= 90:
        print("⚠ WARNING: 90% budget used!")
        print("Advice: Reduce shopping & luxury expenses.")
    elif percent >= 70:
        print("Caution: More than 70% used.")
        print("Advice: Control spending for rest of month.")
    else:
        print("Good: Spending is under control.")


#Display

def show_table(data):
    print("\n====================================================")
    print("ID | DATE       | CATEGORY   | DESCRIPTION   | AMOUNT")
    print("====================================================")

    for r in data:
        print(f"{r[0]:<2} | {r[1]:<10} | {r[2]:<10} | {r[3]:<12} | Rs {r[4]}")

    print("====================================================\n")


# PDF EXPORT


def generate_pdf_report(uid):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
    except ImportError:
        print("\nreportlab not installed. Run: pip install reportlab")
        return

    print("\n========== GENERATE PDF REPORT ==========")
    today = date.today()

    # year input
    while True:
        year_input = input(f"Please enter the year & leave blank to use current year[{today.year}]: ").strip() or str(today.year)
        try:
            year = int(year_input)
            if 2000 <= year <= 2100:
                break
            print("Enter a valid year (2000-2100).")
        except:
            print("Year must be a number.")

    # month input
    while True:
        month_input = input(f"Please enter the month (1-12) or press Enter to use current month[{today.month}]").strip() or str(today.month)
        try:
            month = int(month_input)
            if 1 <= month <= 12:
                break
            print("Month must be between 1 and 12.")
        except:
            print("Month must be a number.")

    month_name = MONTH_NAMES[month]

    # fetch all data inside function
    conn, cur = connect_db()

    cur.execute("""
        SELECT id, date, category, description, amount FROM expenses
        WHERE user_id=? AND strftime('%Y', date)=? AND strftime('%m', date)=?
        ORDER BY date
    """, (uid, str(year), f"{month:02d}"))
    expenses = cur.fetchall()

    cur.execute("""
        SELECT category, SUM(amount) FROM expenses
        WHERE user_id=? AND strftime('%Y', date)=? AND strftime('%m', date)=?
        GROUP BY category ORDER BY SUM(amount) DESC
    """, (uid, str(year), f"{month:02d}"))
    cat_totals = cur.fetchall()

    cur.execute("""
        SELECT COALESCE(SUM(amount), 0) FROM expenses
        WHERE user_id=? AND strftime('%Y', date)=? AND strftime('%m', date)=?
    """, (uid, str(year), f"{month:02d}"))
    spent = cur.fetchone()[0]

    cur.execute("SELECT username FROM users WHERE id=?", (uid,))
    username = cur.fetchone()[0]

    conn.close()

    budget    = get_budget(uid)
    remaining = budget - spent

    if not expenses:
        print(f"\n⚠  No expenses found for {month_name} {year}.")
        return

    filename = f"Report_{username}_{month_name}_{year}.pdf"
    filepath = os.path.join(os.getcwd(), filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Monthly Expense Report - {month_name} {year}", styles["Title"]))
    story.append(Paragraph(f"User: {username}    Generated: {today}", styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # Summary
    story.append(Paragraph("Summary", styles["Heading2"]))
    if budget > 0:
        pct = (spent / budget) * 100
        if spent > budget:
            status = "OVER BUDGET"
        elif pct >= 90:
            status = "CRITICAL (90%+ used)"
        elif pct >= 70:
            status = "CAUTION (70%+ used)"
        else:
            status = "ON TRACK"
    else:
        pct = 0
        status = "No Budget Set"

    summary_data = [
        ["Total Spent", "Monthly Budget", "Remaining", "Status"],
        [
            f"Rs {spent:,.2f}",
            f"Rs {budget:,.2f}" if budget > 0 else "Not Set",
            f"Rs {remaining:,.2f}" if budget > 0 else "-",
            status
        ]
    ]
    summary_table = Table(summary_data, colWidths=[4*cm, 4*cm, 4*cm, 5*cm])
    summary_table.setStyle(TableStyle([
        ("GRID",     (0, 0), (-1, -1), 0.5, (0, 0, 0)),
        ("FONTNAME", (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",    (0, 0), (-1, -1), "CENTER"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.5*cm))

    # Category Breakdown
    story.append(Paragraph("Category Breakdown", styles["Heading2"]))
    cat_rows = [["Category", "Amount (Rs)", "% of Total"]]
    for cat, amt in cat_totals:
        share = (amt / spent * 100) if spent > 0 else 0
        cat_rows.append([cat, f"{amt:,.2f}", f"{share:.1f}%"])

    cat_table = Table(cat_rows, colWidths=[7*cm, 5*cm, 5*cm])
    cat_table.setStyle(TableStyle([
        ("GRID",     (0, 0), (-1, -1), 0.5, (0, 0, 0)),
        ("FONTNAME", (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",    (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(cat_table)
    story.append(Spacer(1, 0.5*cm))

    # Transaction Details
    story.append(Paragraph("Transaction Details", styles["Heading2"]))
    tx_rows = [["ID", "Date", "Category", "Description", "Amount (Rs)"]]
    for r in expenses:
        tx_rows.append([str(r[0]), r[1], r[2], r[3], f"{r[4]:,.2f}"])

    tx_table = Table(tx_rows, colWidths=[1.5*cm, 3*cm, 3*cm, 6*cm, 3.5*cm])
    tx_table.setStyle(TableStyle([
        ("GRID",     (0, 0), (-1, -1), 0.5, (0, 0, 0)),
        ("FONTNAME", (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",    (0, 0), (2, -1),  "CENTER"),
        ("ALIGN",    (4, 0), (4, -1),  "RIGHT"),
    ]))
    story.append(tx_table)
    story.append(Spacer(1, 0.5*cm))

    # same Smart Budget Advisor(same Logic)
    story.append(Paragraph("Smart Budget Advisor", styles["Heading2"]))
    if budget == 0:
        advice = "No budget set. Set a monthly budget to receive spending insights."
    elif spent > budget:
        advice = f"OVER BUDGET by Rs {abs(remaining):,.2f}. Stop unnecessary spending immediately."
    elif pct >= 90:
        advice = f"CRITICAL: {pct:.1f}% of budget used. Only Rs {remaining:,.2f} left."
    elif pct >= 70:
        advice = f"CAUTION: {pct:.1f}% of budget used. Rs {remaining:,.2f} remaining."
    else:
        advice = f"ON TRACK: {pct:.1f}% of budget used. Rs {remaining:,.2f} still available."
    story.append(Paragraph(advice, styles["Normal"]))

    doc.build(story)

    print(f"\n Report generated successfully!")
    print(f"File: {filepath}")



#Main 



create_tables()

print("===== EXPENSE TRACKER =====")

uid = None

while True:
    print("\n1 Register\n2 Login\n3 Exit")
    ch = input("Choice: ")

    if ch == "1":
        u = input("Username: ")
        p = getpass("Password: ")

        # Empty check
        if u == "" or p == "":
            print("Username and Password cannot be empty!")
            continue

        # Minimum 3 characters
        if len(u) < 3 or len(p) < 3:
            print("Username and Password must be at least 3 characters long!")
            continue

        # Numbers not allowed
        if any(ch.isdigit() for ch in u) or any(ch.isdigit() for ch in p):
            print("Username and Password cannot contain numbers!")
            continue

        print("Registered" if register(u, p) else "Already Exists, try another username!")



    elif ch == "2":
        u = input("Username: ")
        p = getpass("Password: ")

        if u == "" or p == "":
            print("Username and Password cannot be empty!")
            continue

        uid = login(u, p)
        if uid:
            print("Login Successful")
            break
        else:
            print("Invalid Login")




    elif ch == "3":
        exit()

    else:
        print("Invalid Choice! Please enter 1, 2 or 3.")




        

while True:

    print("""
================ MENU ================
1 Add Expense
2 View Expenses
3 Update Expense
4 Delete Expense
5 Search
6 Total Expense
7 Set Budget
8 Smart Budget Advisor
9 Generate PDF Report
10 Exit
=====================================
""")

    choice = input("Select: ").strip()

    #ADD EXPENSE
    if choice == "1":
        d = input("Date (YYYY-MM-DD) or (skip) for current date:").strip() or str(date.today())
        

        # Category validation
        while True:
            c = input("Category: ").strip()

            if not c:
                print("Category is required!")
                continue
            

            if not all(word.isalpha() for word in c.split()):
                print("Only letters allowed in category!")
                continue

            break

        desc = input("Description: ").strip()

        # Amount validation
        while True:
            try:
                amt = float(input("Amount: "))
                if amt > 0:
                    break
                print("Amount must be greater than 0!")
            except ValueError:
                print("Enter valid number!")

        add_expense(uid, d, c, desc, amt)
        print("Added")

    #VIEW
    elif choice == "2":
        show_table(fetch_all(uid))


  #UPDATE
    elif choice == "3":
        eid = input("ID: ")

        # check ID exists
        conn, cur = connect_db()
        cur.execute("SELECT id FROM expenses WHERE id=?", (eid,))
        data = cur.fetchone()
        conn.close()

        if not data:
            print("ID not found!")
            continue

        d = input("New Date (YYYY-MM-DD): ")

        c = input("New Category: ")
        if c == "":
            print("Category is required!")
            continue

        desc = input("New Description: ")

        amt_input = input("New Amount: ")

        if amt_input == "":
            print("Amount required!")
            continue

        try:
            amt = float(amt_input)
        except ValueError:
            print("Invalid amount!")
            continue

        update(eid, d, c, desc, amt)
        print("Updated")

#DELETE
    
    elif choice == "4":

        try:
            eid = int(input("ID: "))
        except ValueError:
            print("Invalid ID!")
            continue

        if delete(eid):
            print("Deleted successfully")
        else:
            print("ID not found")

    #SEARCH
    elif choice == "5":
        k = input("Search Category: ").strip()

        if not k:
            print("Enter keyword!")
            continue

        show_table(search(uid, k))

    #TOTAL EXPENSE
    elif choice == "6":
        print("\nTotal Expense:", total(uid))

    #BUDGET
    elif choice == "7":

        while True:
            try:
                b = float(input("Set Budget: "))
                if b > 0:
                    break
                print("Budget must be greater than 0!")
            except ValueError:
                print("Enter valid number!")

        set_budget(uid, b)
        print("Budget Set")

    #ADVISOR 
    elif choice == "8":
        smart_budget_advisor(uid)



    #PDf
    elif choice == "9":
        generate_pdf_report(uid)



    #EXIT
    elif choice == "10":
        print("Goodbye!")
        break

    
    else:
        print("Invalid Choice!")