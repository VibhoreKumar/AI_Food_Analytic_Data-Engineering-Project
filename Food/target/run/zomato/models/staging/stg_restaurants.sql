
  create or replace   view ZOMATO.staging.stg_restaurants
  
   as (
    select
    *
from ZOMATO.RAW.restaurants
  );

