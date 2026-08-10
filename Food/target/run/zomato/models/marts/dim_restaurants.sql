
  
    

        create or replace transient table ZOMATO.marts.dim_restaurants
         as
        (select
    id as restaurant_id,
    name as restaurant_name,
    city,
    cuisine,
    rating,
    rating_count,
    cost as cost_for_two
from ZOMATO.staging.stg_restaurants
        );
      
  