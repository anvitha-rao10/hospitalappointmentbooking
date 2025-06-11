CREATE DATABASE IF NOT EXISTS hospitaldb;
USE hospitaldb;

CREATE TABLE IF NOT EXISTS appointments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),          
    phone VARCHAR(20),
    doctor VARCHAR(100),
    appointment_time DATETIME,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed'
);

CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS doctors (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);
ALTER TABLE doctors ADD COLUMN is_active BOOLEAN DEFAULT TRUE;




