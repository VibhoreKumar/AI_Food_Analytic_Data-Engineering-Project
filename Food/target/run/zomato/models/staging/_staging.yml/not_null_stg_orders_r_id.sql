
    select
      count(*) as failures,
      count(*) != 0 as should_warn,
      count(*) != 0 as should_error
    from (
      
    
  
    
    



select r_id
from "zomato"."staging"."stg_orders"
where r_id is null



  
  
      
    ) dbt_internal_test