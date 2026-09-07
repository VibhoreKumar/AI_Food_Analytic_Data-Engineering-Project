

    MERGE INTO "zomato"."marts"."fact_order_items" AS DBT_INTERNAL_DEST
        USING "fact_order_items__dbt_tmp20260907013844882428" AS DBT_INTERNAL_SOURCE
        
            
                
            
        
        ON (DBT_INTERNAL_SOURCE.order_item_id = DBT_INTERNAL_DEST.order_item_id)
    
    WHEN MATCHED
    THEN
        UPDATE BY NAME
    WHEN NOT MATCHED
        
    THEN
        INSERT BY NAME

  