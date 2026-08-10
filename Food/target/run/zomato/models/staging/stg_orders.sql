
  create or replace   view ZOMATO.staging.stg_orders
  
   as (
    select
    *
from ZOMATO.RAW.orders
  );

