
  
    
    

    create  table
      "zomato"."marts"."mart_daily_city_revenune__dbt_tmp"
  
    as (
      with monthly as (
    select
        date_trunc('month', order_date) as month,
        trim(list_extract(str_split(city, ','), -1)) as city,
        count(*) as orders,
        count_if(is_delivered) as delivered_orders,
        round(count_if(order_status='Cancelled') / nullif(count(*), 0), 4) as cancel_rate,
        sum(case when is_delivered then sales_amount else 0 end) as gmv,
        round(
            sum(case when is_delivered then sales_amount else 0 end)
            / nullif(count_if(is_delivered), 0), 2
        ) as aov
    from "zomato"."marts"."fct_orders"
    group by 1, 2
),
top_cities as (
    select city
    from monthly
    group by city
    order by sum(gmv) desc
    limit 15
)
select m.*
from monthly m
inner join top_cities t on m.city = t.city
order by m.month, m.city
    );
  
  