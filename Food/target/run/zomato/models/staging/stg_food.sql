
  create or replace   view ZOMATO.staging.stg_food
  
   as (
    select
    *
from ZOMATO.RAW.food
  );

