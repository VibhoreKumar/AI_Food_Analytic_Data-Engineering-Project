
  
    
    

    create  table
      "zomato"."marts"."dim_date__dbt_tmp"
  
    as (
      with spine as (
    select unnest(generate_series('2024-01-01'::date, '2026-12-31'::date, interval 1 day)) as date_day
)
select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    strftime(date_day, '%B') as month_name,
    strftime(date_day, '%A') as day_name,
    (dayofweek(date_day) in (0, 6)) as is_weekend
from spine
    );
  
  