
  
    
    

    create  table
      "zomato"."marts"."dim_restaurants__dbt_tmp"
  
    as (
      select
    id as restaurant_id,
    name as restaurant_name,
    city,
    cuisine,
    rating,
    rating_count,
    cost as cost_for_two
from "zomato"."staging"."stg_restaurants"
    );
  
  