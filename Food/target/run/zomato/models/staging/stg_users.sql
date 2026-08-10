
  create or replace   view ZOMATO.staging.stg_users
  
   as (
    select
    *
from ZOMATO.RAW.users
  );

