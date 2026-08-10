
  create or replace   view ZOMATO.staging.stg_order_items
  
   as (
    select
    *
from ZOMATO.RAW.order_items
  );

