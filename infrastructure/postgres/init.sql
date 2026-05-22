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
	user_id SERIAL PRIMARY KEY,
	password_hash VARCHAR(255) NOT NULL,
	FOREIGN KEY (user_id) REFERENCES user_db.users(id)
}

\c orders_db;
CREATE TABLE users {
}
