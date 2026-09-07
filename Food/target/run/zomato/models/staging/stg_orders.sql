
  
  create view "zomato"."staging"."stg_orders__dbt_tmp" as (
    select
    *
from "zomato"."raw"."orders"
  );
