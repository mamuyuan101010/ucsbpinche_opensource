import mysql.connector
from flask import Flask, jsonify, request, render_template, redirect, url_for, session
import bcrypt
from datetime import timedelta
import datetime

app = Flask(__name__)
app.secret_key = 'dev'

# Database configuration
db_config = {
    'user': '******',  # your MySQL username
    'password': '******',  # your MySQL password
    'host': 'localhost',
    'database': 'car_sharing',
    'raise_on_warnings': True
}

# Utility function to connect to the database
def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection
    
# home route
@app.route('/')
def home():
    if 'username' in session:
        # Defaults to 'Guest' if 'username' is not in session
        username = session.get('username', 'Guest')
        # User is logged in, return a JSON response with the username
        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""SELECT 
                        rr.request_id,
                        rr.rider_id,
                        acc.user_name AS rider_username,
                        rr.date,
                        rr.time,
                        rr.start_point,
                        rr.destination,
                        rr.note
                    FROM 
                        ride_request rr
                    JOIN 
                        account acc ON rr.rider_id = acc.user_id;
        """)
        ride_requests = cursor.fetchall()
        cursor.execute("""SELECT 
                        dr.request_id,
                        dr.driver_id,
                        acc.user_name AS driver_username,
                        dr.date,
                        dr.time,
                        dr.start_point,
                        dr.destination,
                        dr.note,
                        car.brand AS car_brand,
                        car.style AS car_style,
                        car.plate AS car_plate
                    FROM 
                        driver_request dr
                    JOIN 
                        account acc ON dr.driver_id = acc.user_id
                    JOIN 
                        car ON acc.user_id = car.user_id;
        """)
        driver_requests = cursor.fetchall()
        return render_template('home.html', username=username, ride_requests=ride_requests, 
                               driver_requests=driver_requests)
    else:
        # User is not logged in, redirect user to login page
        return redirect(url_for('login'))

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Get username and password from the submitted form
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if username or password is missing
        if not username or not password:
            # Return a JSON response indicating missing username or password
            return jsonify({'status': 'error', 'message': 'Missing username or password'}), 400

        # Connect to the database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # Retrieve the account from the database
            cursor.execute("SELECT * FROM account WHERE user_name = %s", (username,))
            account = cursor.fetchone()

            # Check if the account exists and the password is correct
            if account and bcrypt.checkpw(password.encode('utf-8'), account['password'].encode('utf-8')):
                # Store the username in the session
                session['username'] = account['user_name']
                # Store the user_id in the session
                session['user_id'] = account['user_id']
                # Return a JSON response indicating a successful login with a redirection URL
                return redirect(url_for('home'))

            # If login credentials are invalid, return a JSON response indicating the error
            return jsonify({'status': 'error', 'message': 'Invalid username/password'}), 401

        # Ensure that the database connection is closed
        finally:
            cursor.close()
            connection.close()

    # render the get request login form, or generate an error
    return render_template('login.html')




# route for change password
@app.route('/change_password', methods=['GET', 'POST'])
def manage_passwords():
    if request.method == 'GET':
        return render_template('change_password.html')
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        user_name = request.json.get('user_name')
        old_password = request.json.get('old_password').encode('utf-8')
        new_password = request.json.get('new_password').encode('utf-8')

        # Ensure all parameters are provided
        if not user_name or not old_password or not new_password:
            return jsonify({'msg': 'missing_parameters'}), 400

        # Verify the old password
        cursor.execute(
            "SELECT password FROM account WHERE user_name = %s",
            (user_name,)
        )
        account = cursor.fetchone()

        # Check if user exists and old password matches
        if account and bcrypt.checkpw(old_password, account['password'].encode('utf-8')):
            # Hash the new password
            hashed_password = bcrypt.hashpw(new_password, bcrypt.gensalt())

            # Update the password in the database
            cursor.execute(
                "UPDATE account SET password = %s WHERE user_name = %s",
                (hashed_password, user_name)
            )
            connection.commit()
            return jsonify({'msg': 'password_changed'}), 200
        else:
            return jsonify({'msg': 'invalid_credentials'}), 401

    finally:
        cursor.close()
        connection.close()

# route for changing passphrase
@app.route('/change_passphrase', methods=['GET', 'POST'])
def change_passphrase():
    if request.method == 'GET':
        return render_template('change_passphrase.html')
    # connect to database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # request user's username password and new passphrase input
        user_name = request.json.get('user_name')
        password = request.json.get('password').encode('utf-8')
        new_passphrase = request.json.get('new_passphrase')

        # Ensure all parameters are provided
        if not user_name or not password or not new_passphrase:
            return jsonify({'msg': 'missing_parameters'}), 400

        # Verify the password
        cursor.execute(
            "SELECT password FROM account WHERE user_name = %s",
            (user_name,)
        )
        account = cursor.fetchone()

        # Check if user exists and password matches
        if account and bcrypt.checkpw(password, account['password'].encode('utf-8')):
            # Update the passphrase in the database
            cursor.execute(
                "UPDATE account SET user_passphrase = %s WHERE user_name = %s",
                (new_passphrase, user_name)
            )
            connection.commit()
            return jsonify({'msg': 'passphrase_changed'}), 200
        else:
            return jsonify({'msg': 'invalid_credentials'}), 401

    finally:
        cursor.close()
        connection.close()


# route for car
@app.route('/car', methods=['GET', 'POST'])
def manage_cars():
    # check whether user login
    if 'username' in session:
        # get username, store username string in user_name variable
        user_name = session['username']
        # connect to database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            # handle post request
            if request.method == 'POST':
                # request and store user's input
                brand = request.json.get('brand')
                style = request.json.get('style')
                plate = request.json.get('plate')

                # Validate parameters
                if not all([brand, style, plate]):
                    return jsonify({'message': 'Missing car information'}), 400
                # get user's user_id
                cursor.execute('SELECT user_id FROM account WHERE user_name = %s', (user_name,))
                # store cursor's array
                account = cursor.fetchone()
                # error message for not found user_id
                if account is None:
                    return jsonify({'message': 'User not found'}), 404
                # get user_id value from cursor's array
                user_id = account['user_id']
                # Check if the user already has a car
                cursor.execute('SELECT * FROM car WHERE user_id = %s', (user_id,))
                car = cursor.fetchone()

                if car:
                    # Update existing car information
                    cursor.execute(
                        "UPDATE car SET brand = %s, style = %s, plate = %s WHERE user_id = %s",
                        (brand, style, plate, user_id)
                    )
                else:
                    # Insert new car information as no existing record was found
                    cursor.execute(
                        "INSERT INTO car (brand, style, plate, user_id) VALUES (%s, %s, %s, %s)",
                        (brand, style, plate, user_id)
                    )
                # commit connection after insert data
                connection.commit()
                # return succeed add value
                return jsonify({'message': 'Car added successfully'})
            # handle get request
            # let user see the car data they added
            cursor.execute(
                "SELECT car_id, brand, style, plate FROM car WHERE user_id = (SELECT user_id FROM account WHERE user_name = %s)", 
                (user_name,)
            )
            cars = cursor.fetchall()
            # return the user's car data as jsonofy format
            return render_template('manage_cars.html', cars=cars)
        # handle any other exception
        except Exception as e:
            return jsonify({'error': str(e)})
        # close database connection
        finally:
            cursor.close()
            connection.close()
    # handle the situation that user has not login, navigate them to login page
    # because appsmith will be the front end, 
    # We do not need navigation method here in back end
    return jsonify({'message': 'Please login first'})


# route for order
# for this route, we only need get request (
# as user shall not submit data from this route
@app.route('/order', methods=['GET'])
def manage_orders():
    # check if user login
    if 'username' in session:
        # store user's name in user_name variable
        user_name = session['username']
        # connect to database
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        # get all order request
        cursor.execute("""
            SELECT 
                p.user_name AS passenger_name, 
                d.user_name AS driver_name, 
                eo.date, 
                eo.time, 
                eo.start_point, 
                eo.destination, 
                c.brand, 
                c.style, 
                c.plate
            FROM 
                existing_order eo
                JOIN account p ON eo.passenger_id = p.user_id
                JOIN account d ON eo.driver_id = d.user_id
                LEFT JOIN car c ON d.user_id = c.user_id
            WHERE 
                eo.passenger_id = (SELECT user_id FROM account WHERE user_name = %s) 
                OR 
                eo.driver_id = (SELECT user_id FROM account WHERE user_name = %s);
            """, (user_name, user_name))
        orders = cursor.fetchall()
        # disconnect database
        cursor.close()
        connection.close()
        # return jsonify table 
        return render_template('orders.html', orders=orders)
    # handle the situation that user has not login
    return jsonify({'message': 'Please login first'})

@app.route('/ride_request', methods=['GET', 'POST'])
def manage_ride_requests():
    # check whether user login
    if 'username' in session:
        # store username from session
        user_name = session['username']
        # handle post request
        if request.method == 'POST':
            # connect to database
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # request data from the rider
            date = request.form.get('date')
            time = request.form.get('time')
            start_point = request.form.get('start_point')
            destination = request.form.get('destination')
            note = request.form.get('note')
            # insert user's data input into database
            try:
                cursor.execute(
                    """INSERT INTO ride_request (rider_id, date, time, start_point, destination, note)
                       VALUES ((SELECT user_id FROM account WHERE user_name = %s), 
                       %s, %s, %s, %s, %s)""",
                    (user_name, date, time, start_point, destination, note)
                )
                connection.commit()
                return render_template('ride_request_submit_success.html')
            # handle exception error
            except Exception as e:
                connection.rollback()
                return jsonify({'error': str(e)}), 400
            # close database connection
            finally:
                cursor.close()
                connection.close()
        try:
            # make connection
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)
            # Modify this query if you want to fetch only the logged-in user's ride requests
            cursor.execute(
                """SELECT 
                    rr.request_id, rr.date, rr.time, rr.start_point, rr.destination, rr.note
                    FROM 
                    ride_request rr
                    JOIN account a ON rr.rider_id = a.user_id
                    WHERE a.user_name = %s""",
                (user_name,)
            )
            ride_requests = cursor.fetchall()
            # Convert date and time to string
            for ride_request in ride_requests:
                if isinstance(ride_request['date'], datetime.date):
                    ride_request['date'] = ride_request['date'].strftime('%Y-%m-%d')
                
                if isinstance(ride_request['time'], (datetime.time, datetime.datetime)):
                    ride_request['time'] = ride_request['time'].strftime('%H:%M:%S')

            return render_template('ride_requests.html', ride_requests=ride_requests)

        finally:
            cursor.close()
            connection.close()
        
    # handle the unloged situation
    else:
        return jsonify({'message': 'Please login first'})

@app.route('/driver_request', methods=['GET', 'POST'])
def manage_driver_requests():
    if 'username' in session:
        user_name = session['username']

        if request.method == 'POST':
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            date = request.form.get('date')
            time = request.form.get('time')
            start_point = request.form.get('start_point')
            destination = request.form.get('destination')
            note = request.form.get('note')

            try:
                cursor.execute(
                    """INSERT INTO driver_request (driver_id, date, time, start_point, destination, note) 
                    VALUES ((SELECT user_id FROM account WHERE user_name = %s), 
                    %s, %s, %s, %s, %s)""",
                    (user_name, date, time, start_point, destination, note)
                )
                connection.commit()
                return render_template('driver_request_submit_success.html')
            except Exception as e:
                connection.rollback()
                return jsonify({'error': str(e)}), 400
            finally:
                cursor.close()
                connection.close()

        elif request.method == 'GET':
            connection = get_db_connection()
            cursor = connection.cursor(dictionary=True)

            try:
                cursor.execute(
                    """SELECT 
                    dr.request_id, dr.date, dr.time, dr.start_point, dr.destination, dr.note
                    FROM 
                    driver_request dr
                    JOIN account a ON dr.driver_id = a.user_id
                    WHERE a.user_name = %s""",
                    (user_name,)
                )
                driver_requests = cursor.fetchall()
                 # Convert date and time to string
                for driver_request in driver_requests:
                    if isinstance(driver_request['date'], datetime.date):
                        driver_request['date'] = driver_request['date'].strftime('%Y-%m-%d')
                    
                    if isinstance(driver_request['time'], (datetime.time, datetime.datetime)):
                        driver_request['time'] = driver_request['time'].strftime('%H:%M:%S')


                return render_template('driver_requests.html', driver_requests=driver_requests)
            finally:
                cursor.close()
                connection.close()
    else:
        return jsonify({'message': 'Please login first'})


# route for delete driver's request
@app.route('/delete_driver_request/<int:request_id>', methods=['POST'])
def delete_driver_request(request_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'msg': 'unauthorized'}), 401

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Retrieve the user_id associated with the request
        cursor.execute(
            "SELECT driver_id FROM driver_request WHERE request_id = %s",
            (request_id,)
        )
        request = cursor.fetchone()

        # Check if the request exists and belongs to the logged-in user
        if request is None:
            return jsonify({'msg': 'request_not_found'}), 404
        if request['driver_id'] != session['user_id']:
            return jsonify({'msg': 'unauthorized'}), 403

        # Delete the request
        cursor.execute(
            "DELETE FROM driver_request WHERE request_id = %s",
            (request_id,)
        )
        connection.commit()

        if cursor.rowcount == 0:
            return jsonify({'msg': 'no_request_deleted'}), 404

        return render_template('driver_request_deleted.html')

    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return jsonify({'msg': 'error_deleting_request'}), 500

    finally:
        cursor.close()
        connection.close()


# route for delete rider's request
@app.route('/delete_rider_request/<int:request_id>', methods=['POST'])
def delete_rider_request(request_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'msg': 'unauthorized'}), 401
    
    # connect to database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    
    try:
        if request.form.get('_method') == 'DELETE':
            # Retrieve the user_id associated with the request
            cursor.execute(
                "SELECT rider_id FROM ride_request WHERE request_id = %s",
                (request_id,)
            )
            rider_request = cursor.fetchone()

            # Check if the request exists and belongs to the logged-in user
            if rider_request is None:
                return jsonify({'msg': 'request_not_found'}), 404
            if rider_request['rider_id'] != session['user_id']:
                return jsonify({'msg': 'unauthorized'}), 403

            # Delete the request
            cursor.execute(
                "DELETE FROM ride_request WHERE request_id = %s",
                (request_id,)
            )
            connection.commit()

            if cursor.rowcount == 0:
                return jsonify({'msg': 'no_request_deleted'}), 404
            return render_template('rider_request_deleted.html')
        else:
            return jsonify({'msg': 'not in delete method'}), 405
    # handling errors
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return jsonify({'msg': 'error_deleting_request'}), 500
    # close the database
    finally:
        cursor.close()
        connection.close()

# route for a rider to add driver
@app.route('/add_driver/<int:request_id>', methods=['POST'])
def add_driver(request_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'msg': 'unauthorized'}), 401
    # the rider should input the driver's username and password
    # which told by the driver who previously agreed to let the 
    # rider use their car 
    driver_username = request.form.get('driver_username')
    driver_passphrase = request.form.get('driver_passphrase')
    # handle the situation when the user's input is missing
    if not all([driver_username, driver_passphrase]):
        return jsonify({'msg': 'missing_parameters'}), 400
    # connect to database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Authenticate the driver
        cursor.execute(
            "SELECT user_id, user_passphrase FROM account WHERE user_name = %s",
            (driver_username,)
        )
        driver = cursor.fetchone()
        if not driver or driver['user_passphrase'] != driver_passphrase:
            return jsonify({'msg': 'invalid_credentials'}), 401
        # get the rider request table data
        cursor.execute("SELECT * FROM ride_request WHERE request_id = %s", (request_id,))
        ride_request = cursor.fetchone()
        # check whether the rider's id in request equals to the login id
        if not ride_request['rider_id'] or ride_request['rider_id'] != session['user_id']:
            return jsonify({'msg':'unauthorized'}), 401
        # insert the created order to the existing_order table
        cursor.execute("""INSERT INTO existing_order 
                       (passenger_id, driver_id, date, time, start_point, destination)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       """, (session['user_id'], driver['user_id'], ride_request['date'], ride_request['time'],
                             ride_request['start_point'], ride_request['destination']))
        connection.commit()
        # Delete the request from ride_request table
        cursor.execute(
            "DELETE FROM ride_request WHERE request_id = %s",
            (request_id,)
        )
        connection.commit()
        return render_template('rider_order_created.html')
    
    # handling errors
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return jsonify({'msg': 'error_deleting_request'}), 500
    # close database
    finally:
        cursor.close()
        connection.close()

# route for a driver to add a rider
@app.route('/add_rider/<int:request_id>', methods=['POST'])
def add_rider(request_id):
    # Check if the user is logged in
    if 'user_id' not in session:
        return jsonify({'msg': 'unauthorized'}), 401
    # the driver should input the rider's username and password
    # which told by the rider who previously agreed to let the 
    # driver take him or her 
    rider_username = request.form.get('rider_username')
    rider_passphrase = request.form.get('rider_passphrase')
    # handle the situation when the user's input is missing
    if not all([rider_username, rider_passphrase]):
        return jsonify({'msg': 'missing_parameters'}), 400
    # connect to database
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Authenticate the rider
        cursor.execute(
            "SELECT user_id, user_passphrase FROM account WHERE user_name = %s",
            (rider_username,)
        )
        rider = cursor.fetchone()
        if not rider or rider['user_passphrase'] != rider_passphrase:
            return jsonify({'msg': 'invalid_credentials'}), 401
        # get the driver request table data
        cursor.execute("SELECT * FROM driver_request WHERE request_id = %s", (request_id,))
        driver_request = cursor.fetchone()
        # check whether the driver's id in request equals to the login id
        if not driver_request['driver_id'] or driver_request['driver_id'] != session['user_id']:
            return jsonify({'msg':'unauthorized'}), 401
        # insert the created order to the existing_order table
        cursor.execute("""INSERT INTO existing_order 
                       (passenger_id, driver_id, date, time, start_point, destination)
                       VALUES (%s, %s, %s, %s, %s, %s)
                       """, (rider['user_id'], session['user_id'], driver_request['date'], driver_request['time'],
                             driver_request['start_point'], driver_request['destination']))
        connection.commit()
        # Delete the request from driver_request table
        cursor.execute(
            "DELETE FROM driver_request WHERE request_id = %s",
            (request_id,)
        )
        connection.commit()
        return render_template('driver_order_created.html')
    
    # handling errors
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return jsonify({'msg': 'error_deleting_request'}), 500
    # close database
    finally:
        cursor.close()
        connection.close()

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    # Clear the user's session
    session.clear()
    # Redirect to the login page
    return render_template('logout.html')


if __name__ == '__main__':
    app.run(debug=True)
