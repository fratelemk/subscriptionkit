CREATE='''
    CREATE TABLE IF NOT EXISTS subscriptions(
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT "GBP",
        active BOOLEAN NOT NULL DEFAULT TRUE,
        payment_method TEXT NOT NULL,
        renewal_date REAL NOT NULL,
        created_at REAL DEFAULT CURRENT_TIMESTAMP);
'''

SELECT='''
    SELECT 
        name AS Name,
        amount as Amount,
        currency as Currency,
        active as Active,
        payment_method as Method,
        renewal_date as Renewal
    FROM active
'''

VIEW='''
CREATE TEMPORARY VIEW IF NOT EXISTS active AS 
SELECT *
FROM subscriptions 
WHERE active = 0;
'''