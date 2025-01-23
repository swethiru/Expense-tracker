from flask import Flask, send_from_directory, render_template, request, redirect
from flask_mysqldb import MySQL
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'  # or your MySQL host
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Swedha@2004'
app.config['MYSQL_DB'] = 'expense_tracker'

# Initialize MySQL
mysql = MySQL(app)

# Route: Home Page
@app.route('/')
def home():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()

    # Calculate the sum of expenses
    cursor.execute("SELECT SUM(amount) FROM expenses")
    total_expenses = cursor.fetchone()[0] or 0

    # Get the current budget
    cursor.execute("SELECT amount FROM budget")
    budget = cursor.fetchone()
    budget_amount = budget[0] if budget else 0

    cursor.close()
    return render_template('home.html', expenses=expenses, total_expenses=total_expenses, budget_amount=budget_amount)

# Route: Set Budget
@app.route('/set_budget', methods=['GET', 'POST'])
def set_budget():
    if request.method == 'POST':
        budget = request.form['budget']

        # SQL query to insert/update the budget
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM budget")
        existing_budget = cursor.fetchone()

        if existing_budget:
            cursor.execute("UPDATE budget SET amount = %s", (budget,))
        else:
            cursor.execute("INSERT INTO budget (amount) VALUES (%s)", (budget,))

        mysql.connection.commit()
        cursor.close()

        return redirect('/')

    return render_template('set_budget.html')

# Route: Add Expense
@app.route('/add', methods=['GET', 'POST'])
def add_expense():
    if request.method == 'POST':
        # Convert date from string to date object
        try:
            date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."

        amount = float(request.form['amount'])
        category = request.form['category']
        description = request.form['description']

        # SQL query to insert the new expense
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO expenses (date, amount, category, description) VALUES (%s, %s, %s, %s)",
                       (date, amount, category, description))
        mysql.connection.commit()
        cursor.close()

        return redirect('/')

    return render_template('add_expense.html')

# Route: Delete Expense
@app.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_expense(id):
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
        mysql.connection.commit()
    except Exception as e:
        print(f"Error deleting expense: {e}")
    finally:
        cursor.close()
    return redirect('/')

# Route: View Expenses
@app.route('/view', methods=['GET', 'POST'])
def view_expenses():
    cursor = mysql.connection.cursor()

    # Default SQL query
    query = "SELECT * FROM expenses"
    filters = []
    
    if request.method == 'POST':  # If a filter is applied
        filter_date = request.form.get('filter_date')
        filter_category = request.form.get('filter_category')

        # Add filters based on user input
        if filter_date:
            query += " WHERE date = %s"
            filters.append(filter_date)
        if filter_category:
            if "WHERE" in query:
                query += " AND category = %s"
            else:
                query += " WHERE category = %s"
            filters.append(filter_category)

    cursor.execute(query, filters)
    expenses = cursor.fetchall()
    cursor.close()
    return render_template('view.html', expenses=expenses)

@app.route('/dashboard')
def dashboard():
    cursor = mysql.connection.cursor()
    # Sum of expenses per category
    cursor.execute("SELECT category, SUM(amount) FROM expenses GROUP BY category")
    category_data = list(cursor.fetchall())
    cursor.close()

    # Pass data to the template
    return render_template('dashboard.html', category_data=category_data)



# Initialize the database structure (create the table if it doesn't exist)
def create_db():
    cursor = mysql.connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        date DATE,
                        amount FLOAT,
                        category VARCHAR(50),
                        description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS budget (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        amount FLOAT)''')
    mysql.connection.commit()
    cursor.close()

# Call the create_db function to ensure the table is created on the first run
with app.app_context():
    create_db()

if __name__ == '__main__':
    app.run(debug=True)
