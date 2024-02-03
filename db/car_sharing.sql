CREATE DATABASE car_sharing;
CREATE USER 'app_smith_user'@'localhost' IDENTIFIED BY '690407Mmy1234//';
GRANT ALL PRIVILEGES ON car_sharing.* TO 'app_smith_user'@'localhost';
FLUSH PRIVILEGES;

USE car_sharing;

CREATE TABLE account (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    user_name VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    student_id INT,
    email VARCHAR(255),
    user_passphrase VARCHAR(255) NOT NULL
);

INSERT INTO account (user_name, password, student_id, email, user_passphrase)
VALUES
    ('JohnDoe', 'password123', 12345, 'john.doe@example.com', 'passphrase123'),
    ('AliceSmith', 'pass456', NULL, 'alice.smith@example.com', 'passphrase'),
    ('BobJohnson', 'securepwd', 54321, 'bob.johnson@aaa.com', '123');

CREATE TABLE car (
    car_id INT PRIMARY KEY AUTO_INCREMENT,
    brand VARCHAR(255) NOT NULL,
    style VARCHAR(255),
    plate VARCHAR(255) NOT NULL,
    user_id INT,
    FOREIGN KEY (user_id) REFERENCES account(user_id)
);

INSERT INTO car (brand, style, plate, user_id)
VALUES
    ('Toyota', 'Sedan', 'ABC123', 1),
    ('Honda', 'SUV', 'XYZ987', 3);

CREATE TABLE existing_order (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    passenger_id INT,
    driver_id INT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    start_point VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    FOREIGN KEY (passenger_id) REFERENCES account(user_id),
    FOREIGN KEY (driver_id) REFERENCES account(user_id)
);

INSERT INTO existing_order (passenger_id, driver_id, date, time, start_point, destination)
VALUES
    (1, 3, '2023-11-25', '08:30:00', '123 Main St', '456 Elm St'),
    (2, 1, '2023-11-26', '15:45:00', '789 Oak Ave', '101 Pine Rd');

CREATE TABLE driver_request (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    driver_id INT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    start_point VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    note VARCHAR(255) NOT NULL,
    FOREIGN KEY (driver_id) REFERENCES account(user_id)
);

INSERT INTO driver_request (driver_id, date, time, start_point, destination, note)
VALUES
    (1, '2023-11-27', '10:00:00', '500 Maple St', '600 Cedar Rd', 'call me at 123-456-789'),
    (3, '2023-11-28', '14:15:00', '200 Willow Ave', '300 Birch Ln','text me at wechat 1226');

CREATE TABLE ride_request (
    request_id INT PRIMARY KEY AUTO_INCREMENT,
    rider_id INT,
    date DATE NOT NULL,
    time TIME NOT NULL,
    start_point VARCHAR(255) NOT NULL,
    destination VARCHAR(255) NOT NULL,
    note VARCHAR(255) NOT NULL,
    FOREIGN KEY (rider_id) REFERENCES account(user_id)
);

INSERT INTO ride_request (rider_id, date, time, start_point, destination, note)
VALUES
    (2, '2023-11-29', '09:30:00', '400 Oak St', '700 Elm Rd', 'email me at eee@haha.comm'),
    (1, '2023-11-30', '18:00:00', '100 Pine Ave', '800 Cedar St', 'see me at kfc');
