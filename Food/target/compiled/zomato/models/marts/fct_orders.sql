
select
    order_id,
    order_timestamp,
    order_date,
    user_id as customer_id,
    r_id as restaurant_id,
    restaurant_city as city,
    cuisine,
    payment_method,
    order_status,
    case when order_status = 'Delivered' then true else false end as is_delivered,
    items_count,
    sales_qty,
    subtotal,
    discount,
    delivery_fee,
    gst,
    sales_amount,
    customer_rating,
    delivery_time_min
from "zomato"."staging"."stg_orders"

  where order_timestamp > (select coalesce(max(order_timestamp),'1900-01-01'::timestamp) from "zomato"."marts"."fct_orders")
