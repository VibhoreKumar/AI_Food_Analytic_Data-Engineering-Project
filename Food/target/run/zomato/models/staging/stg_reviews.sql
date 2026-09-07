
  
  create view "zomato"."staging"."stg_reviews__dbt_tmp" as (
    select
    *
from "zomato"."raw"."reviews"
  );
