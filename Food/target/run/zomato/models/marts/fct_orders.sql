

    MERGE INTO "zomato"."marts"."fct_orders" AS DBT_INTERNAL_DEST
        USING "fct_orders__dbt_tmp20260907013844899830" AS DBT_INTERNAL_SOURCE
        
            
                
            
        
        ON (DBT_INTERNAL_SOURCE.order_id = DBT_INTERNAL_DEST.order_id)
    
    WHEN MATCHED
    THEN
        UPDATE BY NAME
    WHEN NOT MATCHED
        
    THEN
        INSERT BY NAME

  