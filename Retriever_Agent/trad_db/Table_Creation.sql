CREATE EXTENSION IF NOT EXISTS pgcrypto; -- pgcrypto provides gen_random_uuid(), UUID generator

-- Trigger for updating updated_at with time of update
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- TABLES
-- Branch
-- Customer
-- Account (deposit)
-- Loan
-- Repayment (collections)


CREATE TABLE branches (
    branch_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
    -- UUID PK: globally unique

    branch_name TEXT NOT NULL, 
    -- NOT NULL as a constraint; Branch must have a human-readable name

    city TEXT, 
    -- TEXT is variable-length character string; optional (NULL allowed)

    created_at TIMESTAMP NOT NULL DEFAULT NOW(), 
    -- Row creation timestamp (insert time)

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(), 
    -- Last modification timestamp; update this on every data change

    deleted_at TIMESTAMP 
    -- Soft delete marker; NULL = active, NOT NULL = logically deleted
);

CREATE TRIGGER trg_branches_updated_at
BEFORE UPDATE ON branches
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TABLE customers (
    customer_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    -- Customer's full legal name

    kyc_status TEXT CHECK (kyc_status IN ('PENDING', 'VERIFIED')),
    -- KYC verification state; only allows 'PENDING' or 'VERIFIED', prevents str like 'DONE'

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    -- date and time (no time zone); creation time = row insertion time

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
    -- Soft delete flag for regulatory-safe data retention
);

CREATE TRIGGER trg_customers_updated_at
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TABLE accounts (
    account_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    -- Foreign key to customers (an account must belong to an existing customer)

    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    -- FK to branches (Links account to a branch)

    account_type TEXT CHECK (account_type IN ('SAVINGS', 'CURRENT', 'FD')),
    -- Allowed account categories only

    balance NUMERIC(12,2),
    -- up to 12 digits total, 2 digits after decimal; Avoids floating-point rounding issues

    opened_at DATE,
    -- Date only (no time)

    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE TRIGGER trg_accounts_updated_at
BEFORE UPDATE ON accounts
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TABLE loans (
    loan_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(customer_id),
    branch_id UUID NOT NULL REFERENCES branches(branch_id),
    loan_type TEXT CHECK (loan_type IN ('HOME', 'PERSONAL', 'AUTO')),
    principal NUMERIC(12,2),
    interest_rate NUMERIC(5,2),
    tenure_months INT,
    -- Loan duration in months

    disbursed_at DATE,
    -- Date loan amount was released / given to customer

    status TEXT CHECK (status IN ('ACTIVE', 'CLOSED', 'NPA')),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE TRIGGER trg_loans_updated_at
BEFORE UPDATE ON loans
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE TABLE repayments (
    repayment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    loan_id UUID NOT NULL REFERENCES loans(loan_id),
    due_date DATE,
    paid_date DATE,
    amount_due NUMERIC(12,2),
    amount_paid NUMERIC(12,2),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE TRIGGER trg_repayments_updated_at
BEFORE UPDATE ON repayments
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


-- To exclude deleted rows, queries should always include:
-- WHERE deleted_at IS NULL

