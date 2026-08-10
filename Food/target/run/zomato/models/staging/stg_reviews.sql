
  create or replace   view ZOMATO.staging.stg_reviews
  
   as (
    select
    *
from ZOMATO.RAW.reviews
  );

