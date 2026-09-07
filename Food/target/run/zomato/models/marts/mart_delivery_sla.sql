
  
    
    

    create  table
      "zomato"."marts"."mart_delivery_sla__dbt_tmp"
  
    as (
      with hourly as (
    select
        trim(list_extract(str_split(city, ','), -1)) as city,
        hour(order_timestamp) as order_hour,
        count_if(is_delivered) as delivered_orders,
        round(median(delivery_time_min), 1) as p50,
        round(percentile_cont(0.9) within group (order by delivery_time_min), 1) as p90
    from "zomato"."marts"."fct_orders"
    where is_delivered
    group by 1, 2
),
top_cities as (
    select city
    from hourly
    group by city
    order by sum(delivered_orders) desc
    limit 15
)
select h.*
from hourly h
inner join top_cities t on h.city = t.city
order by h.city, h.order_hour
    );
  
  