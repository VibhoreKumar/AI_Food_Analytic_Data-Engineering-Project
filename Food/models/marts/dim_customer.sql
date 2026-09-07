select
    user_id as customer_id,
    name as customer_name,
    email,
    "Age" as age,
    CASE WHEN "Age" < 25 then 'Gen Z'
         WHEN "Age" < 40 then 'Millennial'
         WHEN "Age" < 55 then 'Gen X'
         WHEN "Age" is null then 'Unknown'
         ELSE 'Boomer' END as age_segment,
    "Gender" as gender,
    "Marital Status" as marital_status,
    "Occupation" as occupation,
    "Monthly Income" as monthly_income,
    "Educational Qualifications" as education,
    "Family size" as family_size
from {{ ref('stg_users') }}