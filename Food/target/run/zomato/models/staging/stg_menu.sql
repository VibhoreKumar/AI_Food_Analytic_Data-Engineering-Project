
  
  create view "zomato"."staging"."stg_menu__dbt_tmp" as (
    select
    *
from "zomato"."raw"."menu"
  );
