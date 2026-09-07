
  
  create view "zomato"."staging"."stg_restaurants__dbt_tmp" as (
    select
    *
from "zomato"."raw"."restaurants"
  );
