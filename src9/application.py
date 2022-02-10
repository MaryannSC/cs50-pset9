import os
import re

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
# export API_KEY=pk_7bcd5b58f4cb40d1b13b4bcd426be30f
os.environ['API_KEY'] = 'pk_7bcd5b58f4cb40d1b13b4bcd426be30f'
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    user_total = 0

    # get stock info from database
    holdings = db.execute(
        "SELECT symbol, SUM(shares) FROM transactions WHERE userid=? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])

    for stock in holdings:
        stock['shares'] = stock['SUM(shares)']
        data = lookup(stock['symbol'])
        if data == None:
            return apology("Symbol not found", 403)
        stock['name'] = data['name']
        stock['current_price'] = usd(data['price'])
        stock['total'] = usd(stock['shares'] * data['price'])
        user_total += stock['shares'] * data['price']

    # get user CASH
    rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
    user_total += rows[0]["cash"]

    return render_template("portfolio.html", holdings=holdings, cash=usd(rows[0]["cash"]), total=usd(user_total))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # get stock symbol entered by user
        buySymbol = request.form.get("symbol")
        if buySymbol == '':
            return apology("You must enter a stock symbol", 403)

        # lookup data for company
        data = lookup(buySymbol)
        if data == None:
            return apology("Symbol not found", 403)

        # get number of shares entered by user
        shares = request.form.get("shares")
        if shares == '':
            return apology("You must enter a value for number of shares", 403)
        shares = int(shares)
        # check shares values
        if shares <= 0:
            return apology("Number of shares must be greater than 0", 403)

        # check if user has enough cash for purchase
        rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        cash = rows[0]["cash"]

        if float(shares) * data["price"] > cash:
            return apology("You do not have enough cash for that purchase!", 403)

        # Make puchase, insert into transactions table
        else:
            db.execute("INSERT INTO transactions (userid, symbol, shares, price) VALUES(?, ?, ?, ?)",
                       session["user_id"], data["symbol"], shares, data["price"])
            # update cash in user table
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash - float(shares)*data["price"], session["user_id"])

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # get stock info from database
    activity = db.execute("SELECT symbol, shares, price, timestamp FROM transactions WHERE userid=?", session["user_id"])
    for transaction in activity:
        transaction['price'] = usd(transaction['price'])

    return render_template("history.html", activity=activity)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        if symbol == '':
            return apology("You must enter a stock symbol")

        data = lookup(symbol)
        if data == None:
            return apology("Symbol not found", 403)

        return render_template("quoted.html", data=data)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Ensure password confirmation was submitted
        elif not request.form.get("confirmation"):
            return apology("must reenter password to confirm", 403)

        # Query database to check if username already exists
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        if len(rows) == 1:
            return apology("username already exists", 403)

        # Check if passwords match
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Check strength of password: must have at least 8 characters, 1 uppercase, 1 lowercase, 1 special character
        password = request.form.get("password")

        # Check length of password
        if len(password) < 8:
            return apology("passwords must have at least 8 characters", 403)
            
        upperRegex = re.compile(r'[A-Z]')
        lowerRegex = re.compile(r'[a-z]')
        numberRegex = re.compile(r'\d')
        specialRegex = re.compile(r'\W')

        if(upperRegex.search(password) == None):
            return apology("passwords must contain at least 1 uppercase character", 403)

        if(lowerRegex.search(password) == None):
            return apology("passwords must contain at least 1 lowercase letter", 403)

        if(numberRegex.search(password) == None):
            return apology("passwords must contain a least 1 number", 403)

        if(specialRegex.search(password) == None):
            return apology("passwords must contain at least 1 special character", 403)


        # Add user to database
        db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", request.form.get("username"),
                   generate_password_hash(password))

        # Query database to get user's id for session
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # get user's stock info from database
    holdings = db.execute(
        "SELECT symbol, SUM(shares) FROM transactions WHERE userid=? GROUP BY symbol HAVING SUM(shares) > 0", session["user_id"])

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        sellSymbol = request.form.get("symbol")
        if sellSymbol == None:
            return apology("Please select a stock symbol")

        sellShares = request.form.get("shares")
        if sellShares == '':
            return apology("Please enter number of shares")
        sellShares = int(sellShares)
        if sellShares < 0:
            return apology("Number of shares must be greater than 0")

        for stock in holdings:
            if stock['symbol'] == sellSymbol:
                ownShares = stock['SUM(shares)']

        # check if user owns sufficient shares
        if sellShares > ownShares:
            return apology(f"You can't sell {sellShares}, you only own {ownShares} shares!")

        # complete transaction
        else:
            # get current price of stock
            data = lookup(sellSymbol)
            if data == None:
                return apology("Symbol not found", 403)

            # update transactions with negative shares of stock
            db.execute("INSERT INTO transactions (userid, symbol, shares, price) VALUES(?, ?, ?, ?)",
                       session["user_id"], data["symbol"], (-1) * int(sellShares), data["price"])

            # get current user CASH
            rows = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
            cash = rows[0]['cash']

            # add to user cash
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + float(sellShares)*data["price"], session["user_id"])

            # Redirect user to home page
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    # Display dropdown of stocks available to sell and get how many shares to sell
    else:
        stockList = []

        for stock in holdings:
            stockList.append(stock['symbol'])

        return render_template("sell.html", stockList=stockList)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
