
  
    

        create or replace transient table ZOMATO.marts.dim_customer
         as
        (select
    user_id as customer_id,
    name as customer_name,
    email,
    age,
    CASE WHEN age < 25 then 'Gen Z'
         WHEN age < 40 then 'Millennial'
         WHEN age < 55 then 'Gen X'
         WHEN age is null then 'Unknown'
         ELSE 'Boomer' END as age_segment,
    gender,
    marital_status,
    occupation,
    monthly_income,
    education,
    family_size
from ZOMATO.staging.stg_users
        );
      
  