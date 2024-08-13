from flask import Flask, render_template, request, redirect, session
import mysql.connector
import io
import os
from flask import Response
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from pymongo import MongoClient
import numpy as np
from sklearn.linear_model import LinearRegression

uri = "mongodb+srv://prabhavbk5112:NxHXaMErItViI3zA@cluster0.tlrsxp2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
# Create a new client and connect to the server
client = MongoClient(uri)
db = client['user_credentials']
collection = db['users']

# Connect to the MySQL database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="admin@123",
    database="personal_finance"
)

# Create a cursor object to interact with the database
cursor = mydb.cursor()

app = Flask(__name__)

SECRET_KEY = os.environ.get('SECRET_KEY') or 'this is a secret'
app.config['SECRET_KEY'] = SECRET_KEY

expenses = []

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html', user_logged_in=session.get('username') is not None)
    if 'username' in session:
        user_logged_in = True
        return redirect('/home')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Check if the user exists in the MongoDB database
    user = db.users.find_one({'username': username, 'password': password})
    if user:
            session['username'] = user['username']
            user_logged_in = True
            return redirect('/home')
            
    user_logged_in = False
    return render_template('login.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('register.html', user_logged_in=session.get('username') is not None)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']
        phone = request.form['phone']
        email = request.form['email']
        budget = request.form['budget']
        print(request.form)
        # Check if the user exists in the MongoDB database
        user = collection.find_one({'username': username})
        if username == "admin":
            return render_template('register.html', error='User already exists')
        else:
            db.users.insert_one({'username': username, 'password': password})
            #Write the proifle details into SQL database
            cursor = mydb.cursor()
            cursor.execute("INSERT INTO profile (Name, Phone, emailID, budget, user) VALUES (%s, %s, %s, %s, %s)", (name, phone, email, budget, username))
            mydb.commit()
            return redirect('/login')

@app.route('/register', methods=['POST'])
def register():
    if 'username' in session:
        return redirect('/home')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if the user exists in the MongoDB database
        user = db.users.find_one({'username': username})
        if user:
            return render_template('register.html', error='User already exists')

        # Insert the user into the MongoDB database
        db.users.insert_one({'username': username, 'password': password})
        return redirect('/login')

    return render_template('register.html')

@app.route('/plot_payMode.png')
#@token_required
def plot_payMode():
    fig = create_payModefig()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

def create_payModefig():
    fig = Figure(figsize=(18, 8), dpi=100)
    axis1 = fig.add_subplot(1, 3, 1)
    axis2 = fig.add_subplot(1, 3, 2)
    axis3 = fig.add_subplot(1, 3, 3)
    
    # Give a title to the figure
    fig.suptitle('Analysis of expenses')
    
    uname = session['username']
    
    # Fetch all the expenses by payment mode from the database
    sql_mode = "SELECT mode, SUM(amount) FROM Expense WHERE user = %s GROUP BY mode"
    cursor_mode = mydb.cursor() 
    cursor_mode.execute(sql_mode, (uname,))
    expenses_mode = cursor_mode.fetchall()
    cursor_mode.close()
    
    # Fetch all the expenses by category from the database
    sql_category = "SELECT category, SUM(amount) FROM Expense WHERE user = %s GROUP BY category"
    cursor_category = mydb.cursor() 
    cursor_category.execute(sql_category, (uname,))
    expenses_category = cursor_category.fetchall()
    cursor_category.close()
    
    # Fetch all the expenses by date from the database
    sql_date = "SELECT date_of_txn, SUM(amount) FROM Expense WHERE user = %s GROUP BY date_of_txn"
    cursor_date = mydb.cursor() 
    cursor_date.execute(sql_date, (uname,))
    expenses_date = cursor_date.fetchall()
    cursor_date.close()
    
    if uname == 'admin':
        # Fetch all the expenses by payment mode from the database for admin user
        sql_mode_admin = "SELECT mode, SUM(amount) FROM Expense GROUP BY mode"
        cursor_mode_admin = mydb.cursor() 
        cursor_mode_admin.execute(sql_mode_admin)
        expenses_mode_admin = cursor_mode_admin.fetchall()
        cursor_mode_admin.close()
        
        # Fetch all the expenses by category from the database for admin user
        sql_category_admin = "SELECT category, SUM(amount) FROM Expense GROUP BY category"
        cursor_category_admin = mydb.cursor() 
        cursor_category_admin.execute(sql_category_admin)
        expenses_category_admin = cursor_category_admin.fetchall()
        cursor_category_admin.close()
        
        # Fetch all the expenses by date from the database for admin user
        sql_date_admin = "SELECT date_of_txn, SUM(amount) FROM Expense GROUP BY date_of_txn"
        cursor_date_admin = mydb.cursor() 
        cursor_date_admin.execute(sql_date_admin)
        expenses_date_admin = cursor_date_admin.fetchall()
        cursor_date_admin.close()
        
        expenses_mode = expenses_mode_admin
        expenses_category = expenses_category_admin
        expenses_date = expenses_date_admin
    
    # Plotting expenses by payment mode
    categories_mode = []
    amounts_mode = []
    for expense in expenses_mode:
        categories_mode.append(expense[0])
        amounts_mode.append(expense[1])
    axis1.pie(amounts_mode, labels=categories_mode, autopct='%1.1f%%')
    axis1.set_title('Expenses by Payment Mode')
    
    # Plotting expenses by category
    categories_category = []
    amounts_category = []
    for expense in expenses_category:
        categories_category.append(expense[0])
        amounts_category.append(expense[1])
    axis2.pie(amounts_category, labels=categories_category, autopct='%1.1f%%')
    axis2.set_title('Expenses by Category')
    
    # Plotting expenses by date
    categories_date = []
    amounts_date = []
    for expense in expenses_date:
        categories_date.append(expense[0])
        amounts_date.append(expense[1])
    axis3.bar(categories_date, amounts_date)
    axis3.tick_params(axis='x', rotation=45)  # Adjust the rotation angle as per your preference
    axis3.set_title('Expenses by Date')
    
    return fig
    
    # Plotting expenses by payment mode
    categories_mode = []
    amounts_mode = []
    for expense in expenses_mode:
        categories_mode.append(expense[0])
        amounts_mode.append(expense[1])
    axis1.pie(amounts_mode, labels=categories_mode, autopct='%1.1f%%')
    
    # Plotting expenses by category
    categories_category = []
    amounts_category = []
    for expense in expenses_category:
        categories_category.append(expense[0])
        amounts_category.append(expense[1])
    axis2.pie(amounts_category, labels=categories_category, autopct='%1.1f%%')
    return fig

@app.route('/reports', methods=['GET'])
def reports():

    uname = session['username']
    
    # Retrieve all the amounts spent grouped by month of expenditure
    cursor = mydb.cursor()
    if uname == 'admin':
        sql = "SELECT MONTH(date_of_txn), SUM(amount) FROM Expense GROUP BY MONTH(date_of_txn)"
        cursor.execute(sql)
    else:
        sql = "SELECT MONTH(date_of_txn), SUM(amount) FROM Expense WHERE user = %s GROUP BY MONTH(date_of_txn)"
        cursor.execute(sql, (session['username'],))

    expenses = cursor.fetchall()
    cursor.close()
    # Get the x and y values for linear regression
    x = [expense[0] for expense in expenses]
    y = [expense[1] for expense in expenses]
    # Convert x to a 2D array
    x = np.array(x).reshape(-1, 1)

    # Create a linear regression model and fit the data
    model = LinearRegression()
    model.fit(x, y)

    # Predict the expenditure for the next month
    next_month = np.array([[len(expenses) + 1]])
    predicted_expenditure = model.predict(next_month)
    
    cursor = mydb.cursor()
    if uname == 'admin':
        cursor.execute("SELECT AVG(budget) FROM profile")
    else:
        cursor.execute("SELECT budget FROM profile WHERE user = %s", (uname,))
    budget = cursor.fetchone()[0]    
    print(budget)
    if predicted_expenditure > budget:
        content = "You will exceed your budget of ₹" + str(budget)
    return render_template('reports.html', expenses=expenses, predicted_expenditure=predicted_expenditure[0], user_logged_in=session.get('username') is not None)
    
@app.route('/home')
def index():
    if 'username' not in session:
        return redirect('/login')

    uname = session['username']
    if uname == 'admin':
        sql = "SELECT * FROM Expense"
        cursor = mydb.cursor()
        cursor.execute(sql)
    else:
        sql = "SELECT * FROM Expense where user = %s"
        cursor = mydb.cursor() 
        cursor.execute(sql, (uname,))
    
    expenses = cursor.fetchall()
    cursor.close() 
    # Return the expenses to the template
    return render_template('index.html', expenses=expenses,user_logged_in=session.get('username') is not None)

@app.route('/new_expense', methods=['GET'])
def new_expense():
    if 'username' not in session:
        return redirect('/login')

    return render_template('new_expense.html',user_logged_in=session.get('username') is not None)

@app.route('/new_loan', methods=['GET'])
def new_loan():
    if 'username' not in session:
        return redirect('/login')
    return render_template('new_loan.html',user_logged_in=session.get('username') is not None)

@app.route('/delete_loan', methods=['POST'])
def delete_loan():
    if 'username' not in session:
        return redirect('/login')

    uname = session['username']

    if request.method == 'POST':
        cursor = mydb.cursor(buffered=True)
        content = "Cleared a loan"
        cursor.execute("SELECT MAX(notify_id) FROM Notification where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            notify_id = 1
        else:
            notify_id = tmp[0] + 1
        nType = "DELETE LOAN"
        cursor.execute("INSERT INTO Notification values(%s, %s, %s, %s)",(notify_id,nType,uname, content))
        
        loanID = request.form['loanID']
        if uname == 'admin':
            sql = "DELETE FROM Loan WHERE loan_num = %s"
            values = (loanID,)
        else:
            sql = "DELETE FROM Loan WHERE loan_num = %s AND user = %s"
            values = (loanID, uname)
        cursor.execute(sql, values)
        
        if uname == 'admin':
            sql = "SELECT loan_num FROM Loan ORDER BY loan_num"
            cursor.execute(sql)
        else:
            sql = "SELECT loan_num FROM Loan WHERE user = %s ORDER BY loan_num"
            cursor.execute(sql, (uname,))
        loans = cursor.fetchall()
        for i, loan in enumerate(loans, start=1):
            if uname == 'admin':
                sql = "UPDATE Loan SET loan_num = %s WHERE loan_num = %s"
                values = (i, loan[0])
            else:
                sql = "UPDATE Loan SET loan_num = %s WHERE loan_num = %s AND user = %s"
                values = (i, loan[0], uname)
            cursor.execute(sql, values)
        cursor.close()
        mydb.commit()
        return redirect('/loans')

@app.route('/add_loan', methods=['POST'])
def add_loan():
    if 'username' not in session:
        return redirect('/login')

    uname = session['username']

    if request.method == 'POST':
        cursor = mydb.cursor(buffered=True)
        cursor.execute("SELECT MAX(loan_num) FROM Loan where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            loanID = 1
        else:
            loanID = tmp[0] + 1
        
        cursor.execute("SELECT MAX(loan_num) FROM Loan where user = %s",(uname,))
        amount = request.form['loan_amount']
        interest = request.form['interest']
        endDate = request.form['endDate']
        startDate = request.form['startDate']
        dueDate = request.form['dueDate']
        balance = request.form['balance']
        loan_type = request.form['type']
        content = "Added a loan of amount " + amount + " at an interest rate of " + interest + "%"
        cursor.execute("SELECT MAX(notify_id) FROM Notification where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            notify_id = 1
        else:
            notify_id = tmp[0] + 1
        nType = "ADD LOAN"
        cursor.execute("INSERT INTO Notification values(%s, %s, %s, %s)",(notify_id,nType,uname, content))
        
        if uname == 'admin':
            sql = "INSERT INTO Loan (loan_num, loan_amount, interest, balance, endDate, startDate, type, dueDate) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
            values = (loanID, amount, interest, balance, endDate, startDate, loan_type, dueDate)
        else:
            sql = "INSERT INTO Loan (loan_num, loan_amount, interest, balance, endDate, startDate, type, dueDate, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
            values = (loanID, amount, interest, balance, endDate, startDate, loan_type, dueDate, uname)
        cursor.execute(sql, values)
        cursor.close()
        mydb.commit()

        return redirect('/loans')

@app.route('/', methods=['GET'])
def home_screen():
    return redirect('/login')

@app.route('/profile', methods=['GET'])
def profile_screen():
    if 'username' not in session:
        return redirect('/login')
    uname = session['username']
    if uname == 'admin':
        sql = "SELECT * FROM profile"
        cursor = mydb.cursor()
        cursor.execute(sql)
    else:
        sql = "SELECT * FROM profile WHERE user = %s"
        cursor = mydb.cursor()
        cursor.execute(sql, (uname,))
    profile = cursor.fetchall()
    cursor.close()

    if uname == 'admin':
        profiles = []
        for p in profile:
            profile_data = {
                'name': p[0],
                'phone': p[1],
                'email': p[2],
                'budget': p[3],
                'user': p[-1]
            }
            profiles.append(profile_data)
        return render_template('profile.html', profiles=profiles, user_logged_in=session.get('username') is not None)
    else:
        profile = {
            'name': profile[0][0],
            'phone': profile[0][1],
            'email': profile[0][2],
            'budget': profile[0][3],
            'user': profile[0][-1]
        }
        return render_template('profile.html', profiles=[profile], user_logged_in=session.get('username') is not None)

@app.route('/notifications',methods=['GET'])
def notifications():
    if 'username' not in session:
        return redirect('/login')
    uname = session['username']
    if uname == 'admin':
        sql = "SELECT * FROM Notification"
        cursor = mydb.cursor() 
        cursor.execute(sql)
    else:
        sql = "SELECT * FROM Notification where user = %s"
        cursor = mydb.cursor() 
        cursor.execute(sql, (uname,))
    notifications = cursor.fetchall()
    print(notifications)
    cursor.close() 
    return render_template('notifications.html', notifications=notifications,user_logged_in=session.get('username') is not None)


@app.route('/add_expense', methods=['POST'])
def add_expense():
    if 'username' not in session:
        return redirect('/login')
    
    uname = session['username']

    if request.method == 'POST':
        cursor = mydb.cursor()
        cursor.execute("SELECT MAX(expenseID) FROM Expense where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            expenseID = 1
        else:
            expenseID = tmp[0] + 1
        amount = request.form['amount']
        category = request.form['category']
        content = "Added an expense of amount " + amount
        cursor.execute("SELECT MAX(notify_id) FROM Notification where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            notify_id = 1
        else:
            notify_id = tmp[0] + 1
        nType = "ADD EXPENSE"
        cursor.execute("INSERT INTO Notification values(%s, %s, %s, %s)",(notify_id,nType,uname, content))
        paymentMode = request.form['paymentMode']
        date = request.form['date']
        if uname == 'admin':
            sql = "INSERT INTO Expense (expenseID, amount, category, date_of_txn, mode) VALUES (%s, %s, %s, %s, %s)"
            values = (expenseID, amount, category, date, paymentMode)
        else:
            sql = "INSERT INTO Expense (expenseID, amount, category, date_of_txn, mode, user) VALUES (%s, %s, %s, %s, %s, %s)"
            values = (expenseID, amount, category, date, paymentMode, uname)
        cursor.execute(sql, values)
        cursor.close()
        mydb.commit()

        return redirect('/home')

@app.route('/loans/', methods=['GET'])
def get_loans():
    if 'username' not in session:
        return redirect('/login')
    uname = session['username']
    if uname == 'admin':
        sql = "SELECT * FROM Loan"
        cursor = mydb.cursor()
        cursor.execute(sql)
    else:
        sql = "SELECT * FROM Loan WHERE user = %s"
        cursor = mydb.cursor()
        cursor.execute(sql, (uname,))
    loans = cursor.fetchall()
    cursor.close()
    return render_template('loans.html', loans=loans,user_logged_in=session.get('username') is not None)

@app.route('/delete_expense', methods=['POST'])
def delete_expense():
    if 'username' not in session:
        return redirect('/login')

    uname = session['username']

    if request.method == 'POST':
        response = request.form
        expenseID = response['expenseID']
        if uname == 'admin':
            sql = "DELETE FROM Expense WHERE expenseID = %s"
            values = (expenseID,)
        else:
            sql = "DELETE FROM Expense WHERE expenseID = %s AND user = %s"
            values = (expenseID,uname)
        cursor.execute(sql, values)
        
        if uname == 'admin':
            sql = "SELECT expenseID FROM Expense ORDER BY expenseID"
            cursor.execute(sql)
        else:
            sql = "SELECT expenseID FROM Expense WHERE user = %s ORDER BY expenseID"
            cursor.execute(sql, (uname,))
        content = "Deleted an expense"
        cursor.execute("SELECT MAX(notify_id) FROM Notification where user = %s",(uname,))
        tmp = cursor.fetchone()
        print(tmp)
        if tmp == (None,):
            notify_id = 1
        else:
            notify_id = tmp[0] + 1
        nType = "DELETE EXPENSE"
        cursor.execute("INSERT INTO Notification values(%s, %s, %s, %s)",(notify_id,nType,uname, content))
        expenses = cursor.fetchall()
        for i, expense in enumerate(expenses, start=1):
            if uname == 'admin':
                sql = "UPDATE Expense SET expenseID = %s WHERE expenseID = %s"
                values = (i, expense[0])
            else:
                sql = "UPDATE Expense SET expenseID = %s WHERE expenseID = %s AND user = %s"
                values = (i, expense[0],uname)
            cursor.execute(sql, values)
        mydb.commit()
        return redirect('/home')

if __name__ == '__main__':
    app.run(debug=True)
