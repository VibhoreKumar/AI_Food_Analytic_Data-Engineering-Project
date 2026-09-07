
  
  create view "zomato"."staging"."stg_order_items__dbt_tmp" as (
    select
    *
from "zomato"."raw"."order_items"
  );
