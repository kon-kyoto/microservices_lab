CREATE DATABASE auth_db;
CREATE DATABASE users_db;
CREATE DATABASE orders_db;

\c users_db;
CREATE TABLE users {
	id SERIAL PRIMARY KEY,
	username VARCHAR(100) UNIQUE NOT NULL,
	email VARCHAR(255) UNIQUE NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
}

\c auth_db;
CREATE TABLE users {
}

\c orders_db;
CREATE TABLE users {
}
