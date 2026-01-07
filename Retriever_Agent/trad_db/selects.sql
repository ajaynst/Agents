select * from branches;

select * from accounts;

select * from loans;

select * from customers;

select * from repayments;

truncate table accounts, loans, repayments, customers, branches;

drop table accounts, loans, repayments, customers, branches;

SHOW search_path;

SELECT schemaname, tablename
FROM pg_catalog.pg_tables;


-- query to show all tables only
SELECT tablename FROM pg_catalog.pg_tables
WHERE schemaname != 'pg_catalog' AND 
    schemaname != 'information_schema';
    

-- cust with verified KYC
SELECT *
FROM customers
WHERE kyc_status = 'VERIFIED';


-- Deposit accounts of specific types
SELECT *
FROM accounts
WHERE account_type IN ('SAVINGS', 'FD');


-- Loans disbursed in a date range
SELECT *
FROM loans
WHERE disbursed_at BETWEEN '2023-01-01' AND '2023-12-31';

-- show all the customers (names only) having balance more than 50k across all types of accounts
SELECT c.customer_id, c.full_name
FROM customers c
JOIN accounts a ON a.customer_id = c.customer_id
WHERE c.deleted_at IS NULL AND a.deleted_at IS NULL
GROUP BY c.customer_id, c.full_name
HAVING SUM(a.balance) > 50000;

-- query from llm (for the above question)
SELECT c.full_name, SUM(a.balance) as total_balance 
FROM customers c 
JOIN accounts a ON c.customer_id = a.customer_id 
GROUP BY c.full_name 
HAVING SUM(a.balance) > 50000;


-- show me the top 5 branch wrt total deposits
SELECT b.branch_name, SUM(a.balance) AS total_deposits
FROM branches b
JOIN accounts a ON a.branch_id = b.branch_id
WHERE b.deleted_at IS NULL AND a.deleted_at IS NULL
GROUP BY b.branch_name
ORDER BY total_deposits DESC;


-- show active and closed loans branchwise
SELECT b.branch_name, l.status, COUNT(*) AS loan_count
FROM branches b
JOIN loans l ON l.branch_id = b.branch_id
WHERE l.status = 'ACTIVE' or l.status = 'CLOSED'
	and b.deleted_at IS NULL 
	and l.deleted_at IS null
GROUP BY b.branch_name, l.status
ORDER BY loan_count DESC;


-- show the details of loans with overdue repayments
SELECT l.loan_id, c.full_name, r.due_date, r.amount_due, r.amount_paid
FROM repayments r
JOIN loans l ON l.loan_id = r.loan_id
JOIN customers c ON c.customer_id = l.customer_id
WHERE r.due_date < CURRENT_DATE
  AND r.amount_paid < r.amount_due
  AND r.deleted_at IS NULL
  AND l.deleted_at IS NULL;


