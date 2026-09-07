
  
    
    

    create  table
      "zomato"."marts"."dim_food__dbt_tmp"
  
    as (
      select
    f_id,
    item as food_name,
    veg_or_non_veg
from "zomato"."staging"."stg_food"
    );
  
  