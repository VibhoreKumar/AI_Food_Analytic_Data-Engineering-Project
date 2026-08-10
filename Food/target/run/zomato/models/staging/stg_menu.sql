
  create or replace   view ZOMATO.staging.stg_menu
  
   as (
    select
    *
from ZOMATO.RAW.menu
  );

