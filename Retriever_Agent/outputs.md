> model hallucinated currency symbol

**Before:**

================================[1m Human Message [0m=================================

whats the sum of outstanding loan amount of all customer?
==================================[1m Ai Message [0m==================================
Tool Calls:
...

[(Decimal('30788152.00'),)]
==================================[1m Ai Message [0m==================================

The sum of outstanding loan amount of all customers is **$30,788,152.00. --> amount in USD**


---------
added "Currency is INR" in schema txt (or can be added in system prompt also)
---------

**After:**

================================[1m Human Message [0m=================================

whats the sum of outstanding loan amount of all customer?
==================================[1m Ai Message [0m==================================
Tool Calls:

[(Decimal('30788152.00'),)]
==================================[1m Ai Message [0m==================================

The sum of outstanding loan amount of all customers is **₹ 30,788,152.00. --> amount in INR**