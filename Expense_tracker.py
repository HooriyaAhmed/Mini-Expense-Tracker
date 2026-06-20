import sqlite3
import os
from datetime import date
import hashlib
from getpass import getpass



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
9 Exit
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



  



    #EXIT
    elif choice == "9":
        print("Goodbye!")
        break

    
    else:
        print("Invalid Choice!")