
select
    oi.order_item_id,
    oi.order_id,
    oi.r_id as restaurant_id,
    oi.f_id,
    o.order_timestamp as order_ts,
    o.order_date,
    o.restaurant_city as city,
    oi.price,
    oi.quantity,
    oi.line_amount
from "zomato"."staging"."stg_order_items" oi
inner join "zomato"."staging"."stg_orders" o using (order_id)

  where o.order_timestamp > (select coalesce(max(order_ts),'1900-01-01'::timestamp) from "zomato"."marts"."fact_order_items")
