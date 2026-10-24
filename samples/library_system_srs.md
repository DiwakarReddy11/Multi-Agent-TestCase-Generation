# Software Requirements Specification: City Library Management System

## 1 Introduction

### 1.1 Purpose
This document specifies the requirements for the City Library Management System (CLMS),
which lets members search the catalogue, borrow and return books, and pay fines online.

### 1.2 Users
- Member: a registered library user.
- Librarian: staff who manage books and members.
- Administrator: staff who manage system settings.

## 2 Functional Requirements

### 2.1 Account Management
FR-1: The system shall allow a visitor to register as a member with name, email and password.
FR-2: The password shall be at least 8 characters and contain at least one digit.
FR-3: The system shall lock a member account for 15 minutes after 5 consecutive failed login attempts.
FR-4: The system shall let a member reset their password through a link sent to their registered email. The link shall expire after 30 minutes.

### 2.2 Catalogue Search
FR-5: The system shall let any user search books by title, author or ISBN.
FR-6: Search results shall show availability (available, on loan, reserved) for each copy.

### 2.3 Borrowing and Returns
FR-7: A member shall be able to borrow at most 5 books at the same time.
FR-8: The standard loan period shall be 14 days.
FR-9: A member shall be able to renew a loan once, for 7 more days, unless another member has reserved the book.
FR-10: The system shall charge a fine of 10 INR per day for each overdue book, up to a maximum of 500 INR per book.
FR-11: A member with unpaid fines above 200 INR shall not be able to borrow books.

### 2.4 Reservations
FR-12: A member shall be able to reserve a book that is currently on loan.
FR-13: When a reserved book is returned, the system shall email the first member in the reservation queue and hold the book for 3 days.

## 3 Non-Functional Requirements

### 3.1 Performance
NFR-1: Catalogue search shall return results within 2 seconds for 95% of requests with up to 500 concurrent users.

### 3.2 Security
NFR-2: Passwords shall be stored hashed with bcrypt; plain-text passwords shall never be stored or logged.
NFR-3: All pages shall be served over HTTPS.

### 3.3 Availability
NFR-4: The system shall be available 99.5% of the time each month, excluding planned maintenance announced 48 hours in advance.
