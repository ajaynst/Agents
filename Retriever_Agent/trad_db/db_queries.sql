SELECT
    c.full_name,
    COALESCE(SUM(a.balance), 0) AS total_deposits, -- if sum() is null, coalesce will return 0
    COALESCE(SUM(
        CASE WHEN l.status = 'ACTIVE' THEN l.principal ELSE 0 END
    ), 0) AS total_active_loan_principal
FROM customers c
LEFT JOIN accounts a
    ON a.customer_id = c.customer_id
    AND a.deleted_at IS NULL
LEFT JOIN loans l
    ON l.customer_id = c.customer_id
    AND l.deleted_at IS NULL
WHERE c.deleted_at IS NULL
GROUP BY c.customer_id, c.full_name;


select * from loans;