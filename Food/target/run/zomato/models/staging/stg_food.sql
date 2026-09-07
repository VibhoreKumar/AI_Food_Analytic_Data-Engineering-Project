
  
  create view "zomato"."staging"."stg_food__dbt_tmp" as (
    select
    *
from "zomato"."raw"."food"
  );
