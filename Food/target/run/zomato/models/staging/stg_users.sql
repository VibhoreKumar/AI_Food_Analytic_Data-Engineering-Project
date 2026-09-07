
  
  create view "zomato"."staging"."stg_users__dbt_tmp" as (
    select
    *
from "zomato"."raw"."users"
  );
